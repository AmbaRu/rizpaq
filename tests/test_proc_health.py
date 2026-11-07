
















from __future__ import annotations

import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.proc_health import (              
    CPU_BUSY_FLOOR,
    CPU_BUSY_RATIO,
    STALL_TIMEOUT,
    STALL_TIMEOUT_BUSY,
    Liveness,
    make_cpu_reader,
)

                                               
 
                                                                           
                                                                        
                                                                           
                                                                       
                                                                     
BUSY_LOOP = (
    "import time\n"
    "t = time.process_time()\n"
    "x = 1\n"
    "for _i in range(6_000_000):\n"
    "    x = (x * 1103515245 + 12345) & 0x7FFFFFFF\n"
    "print('CHILD_CPU', time.process_time() - t, x)\n"
)

                                                                              
                                                                    
LONG_BUSY_LOOP = (
    "import time\n"
    "t = time.process_time()\n"
    "x = 1\n"
    "for _i in range(20_000_000):\n"
    "    x = (x * 1103515245 + 12345) & 0x7FFFFFFF\n"
    "print('CHILD_CPU', time.process_time() - t, x)\n"
)


class FakeClock:
    pass

    def __init__(self, t=0.0):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt
        return self.t


class TestLivenessDecision(unittest.TestCase):
    pass






    def _liv(self, cpu_series, clock):
        pass
        it = iter(cpu_series)

        def reader():
            try:
                return next(it)
            except StopIteration:
                return cpu_series[-1] if cpu_series else 0.0

        return Liveness(reader, now=clock)

    def test_silent_and_idle_is_a_stall(self):
        pass
        clock = FakeClock()
        liv = self._liv([0.0] * 40, clock)
        for _ in range(40):
            clock.advance(1.0)
            liv.verdict()
        self.assertGreater(liv.last_silent, STALL_TIMEOUT)
        self.assertFalse(liv.busy, "простой не должен считаться работой")
        self.assertTrue(liv.stalled, "молчание при простое обязано сработать")

    def test_silent_but_working_is_not_a_stall(self):
        pass





        clock = FakeClock()
                                                           
        liv = self._liv([0.9 * i for i in range(200)], clock)
        for _ in range(60):                         
            clock.advance(1.0)
            liv.verdict()
            self.assertFalse(
                liv.stalled,
                f"работающий движок убит на {liv.last_silent:.0f} с молчания")
        self.assertTrue(liv.busy, "растущий процессор должен считаться работой")
        self.assertGreater(liv.last_silent, STALL_TIMEOUT)

    def test_working_too_long_eventually_stalls(self):
        pass





        clock = FakeClock()
        liv = self._liv([0.9 * i for i in range(2000)], clock)
        for _ in range(int(STALL_TIMEOUT_BUSY) + 30):
            clock.advance(1.0)
            liv.verdict()
        self.assertTrue(liv.busy, "процессор всё ещё растёт")
        self.assertTrue(liv.stalled, "работающий процесс тоже имеет предел")

    def test_data_resets_silence_and_busy(self):
        pass
        clock = FakeClock()
        liv = self._liv([0.9 * i for i in range(200)], clock)
        for _ in range(40):
            clock.advance(1.0)
            liv.verdict()
        liv.note_data()
        clock.advance(0.5)
        liv.verdict()
        self.assertLess(liv.last_silent, 1.0, "данные должны сбрасывать молчание")
        self.assertFalse(liv.stalled)

    def test_cpu_below_ratio_counts_as_idle(self):
        pass







        clock = FakeClock()
                                                        
        liv = self._liv([0.05 * i for i in range(400)], clock)
        for _ in range(int(STALL_TIMEOUT) + 10):
            clock.advance(1.0)
            liv.verdict()
        self.assertLess(liv.last_cpu_delta,
                        CPU_BUSY_RATIO * liv.last_silent)
        self.assertTrue(liv.stalled, "простой обязан обнаруживаться")

    def test_busy_ratio_uses_the_whole_silence(self):
        pass






        clock = FakeClock()
                                                
        liv = self._liv([0.3 * i for i in range(400)], clock)
        for _ in range(20):
            clock.advance(1.0)
            liv.verdict()
        self.assertAlmostEqual(
            liv.last_cpu_delta / liv.last_silent, 0.3, delta=0.02)
        self.assertTrue(liv.busy)

    def test_floor_protects_against_tiny_growth(self):
        pass








        from unittest import mock

        with mock.patch("core.proc_health.CPU_SAMPLE_INTERVAL", 0.05):
            clock = FakeClock()
                                                               
            liv = self._liv([0.0, 0.03], clock)
            for _ in range(2):
                clock.advance(0.05)
                liv.verdict()
        self.assertLess(liv.last_silent, 0.2)
        self.assertGreater(
            liv.last_cpu_delta, CPU_BUSY_RATIO * liv.last_silent,
            "по доле процесс выглядит работающим — иначе пол не проверяется")
        self.assertLess(liv.last_cpu_delta, CPU_BUSY_FLOOR)
        self.assertFalse(liv.busy, "пол должен удержать процесс в простое")

    def test_ratio_does_not_decay_between_samples(self):
        pass








        clock = FakeClock()
                                              
        liv = self._liv([0.3 * i for i in range(100)], clock)
        for _ in range(20):
            clock.advance(1.0)
            liv.verdict()
        self.assertTrue(liv.busy)
                                                                          
        self.assertGreater(liv.last_silent, 10.0)
        self.assertTrue(liv.busy, "вердикт не должен вытекать со временем")

    def test_data_restarts_the_cpu_accounting_window(self):
        pass








        from unittest import mock

        with mock.patch("core.proc_health.CPU_SAMPLE_INTERVAL", 0.25):
            clock = FakeClock()
                                                             
            liv = self._liv([0.9 * i for i in range(200)], clock)
            for _ in range(20):
                clock.advance(1.0)
                liv.verdict()
            self.assertTrue(liv.busy, "начало: процесс работает")

                                                                     
            self._reset_reader(liv, 20.0)
            liv.note_data()
            for _ in range(int(STALL_TIMEOUT) + 5):
                clock.advance(1.0)
                liv.verdict()
        self.assertGreater(
            liv.last_silent, STALL_TIMEOUT,
            "тест не дождался предела молчания")
        self.assertTrue(
            liv.stalled,
            "процесс, который поработал и затих, не признан простаивающим — "
            "защита не сработает на зависании после работы")

    @staticmethod
    def _reset_reader(liv, base):
        pass
        counter = {"v": base}

        def reader():
            return counter["v"]

        liv._cpu = reader
        liv._cpu_sampled = base
        liv._cpu_val = base
        liv._sample_at = liv._now()

    def test_describe_mentions_state(self):
        pass
        clock = FakeClock()
        liv = self._liv([0.9 * i for i in range(50)], clock)
        for _ in range(5):
            clock.advance(1.0)
            liv.verdict()
        text = liv.describe()
        self.assertIn("молчал", text)
        self.assertTrue("работал" in text or "простаивал" in text, text)


class TestRealCpuReading(unittest.TestCase):
    pass







    def test_cpu_time_grows_for_a_working_child(self):
        pass






        p = subprocess.Popen([sys.executable, "-c", BUSY_LOOP],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            read = make_cpu_reader(p)
            first = read()
            out, _ = p.communicate(timeout=120)
            last = read()
        finally:
            if p.poll() is None:
                p.kill()
        child_cpu = None
        for ln in out.decode("utf-8", "replace").splitlines():
            if ln.startswith("CHILD_CPU"):
                child_cpu = float(ln.split()[1])
        self.assertIsNotNone(child_cpu, f"потомок не отчитался: {out!r}")
        self.assertGreater(
            child_cpu, 0.3,
            f"потомок оказался не нагружен: {child_cpu} с — тест проверяет "
            f"не то. Проверка прибора на неработающем процессе бессмысленна.")
        self.assertGreater(
            last - first, child_cpu * 0.5,
            f"прибор показал {last - first:.2f} с, потомок занял "
            f"{child_cpu:.2f} с — прибор занижает в разы.")

    def test_cpu_time_stable_for_a_sleeping_child(self):
        pass
        p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(4)"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            read = make_cpu_reader(p)
            first = read()
            time.sleep(1.0)
            middle = read()
            p.wait(timeout=30)
        finally:
            if p.poll() is None:
                p.kill()
        self.assertLess(
            middle - first, 0.3,
            f"спящий процесс набрал процессорного времени: {first} -> {middle}")


class TestGuardConstants(unittest.TestCase):
    pass

    def test_limits_are_ordered(self):
        self.assertLess(STALL_TIMEOUT, STALL_TIMEOUT_BUSY,
                        "работающему процессу предел должен быть больше")

    def test_idle_limit_is_unchanged(self):
        pass
        self.assertEqual(STALL_TIMEOUT, 20)

    def test_busy_limit_covers_the_measured_pause(self):
        pass





        measured = 50.5
        self.assertGreater(
            STALL_TIMEOUT_BUSY, measured * 4,
            f"предел {STALL_TIMEOUT_BUSY} с близок к замеренной паузе "
            f"{measured} с — на больших объёмах снова убьёт рабочий движок")


class TestRunZpaqGuard(unittest.TestCase):
    pass















    def setUp(self):
        import core.zpaq_cli as zc

        self.zc = zc
        real = zc.STALL_TIMEOUT
        zc.STALL_TIMEOUT = 1
        self.addCleanup(setattr, zc, "STALL_TIMEOUT", real)

    def _child(self, source):
        return [sys.executable, "-u", "-c", source]

    def test_silent_idle_child_is_stopped(self):
        pass
        rc, text = self.zc.run_zpaq(self._child("import time; time.sleep(60)"))
        self.assertNotEqual(rc, 0, f"зависший процесс не остановлен: {text[-200:]}")
        self.assertIn("простаивал", text,
                      f"причина названа неверно: {text[-300:]}")

    def test_silent_working_child_is_allowed_to_finish(self):
        pass





        rc, text = self.zc.run_zpaq(self._child(LONG_BUSY_LOOP))
        self.assertEqual(rc, 0, f"работающий движок прерван: {text[-300:]}")
        self.assertIn("CHILD_CPU", text, f"вывод потерян: {text[-200:]}")

    def test_output_arriving_resets_the_silence(self):
        pass
        src = (
            "import sys, time\n"
            "for i in range(4):\n"
            "    sys.stdout.write('строка %d\\n' % i)\n"
            "    sys.stdout.flush()\n"
            "    time.sleep(0.4)\n"
        )
        rc, text = self.zc.run_zpaq(self._child(src))
        self.assertEqual(rc, 0, text[-300:])
        for i in range(4):
            self.assertIn(f"строка {i}", text)

    def test_password_prompt_is_named(self):
        pass
        src = (
            "import sys, time\n"
            "sys.stdout.write('Archive is AES-encrypted\\n')\n"
            "sys.stdout.write('Enter AES password:  :\\n')\n"
            "sys.stdout.flush()\n"
            "time.sleep(60)\n"
        )
        rc, text = self.zc.run_zpaq(self._child(src))
        self.assertNotEqual(rc, 0)
        self.assertIn("пароль", text.lower(), text[-300:])


if __name__ == "__main__":
    unittest.main()
