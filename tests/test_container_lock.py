






































from __future__ import annotations

import json
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.container_lock import (              
    DEFAULT_TIMEOUT_S,
    LOCK_SUFFIX,
    POLL_INTERVAL_S,
    ContainerLockBusy,
    container_is_locked,
    container_lock,
    lock_path_for,
)
from core.tasks import (              
    CONTAINER_NAME,
    ContainerLockBusy as TasksContainerLockBusy,             
    add_work,
    container_path,
    empty_container,
    load_container,
    save_container,
    update_container,
    update_job_meta,
)


                                                                  
                                                                  
                                                               
TEST_TIMEOUT_S = 0.3


class _TmpContainer(unittest.TestCase):
    pass

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="rizpaq_lock_test_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.path = container_path(self.dir)


                                                                             
                                                                
                                                                             

class TestBasicLock(_TmpContainer):
    def test_lock_created_and_released(self):
        pass
        lp = lock_path_for(self.path)
        self.assertFalse(lp.exists(), "файла-замка нет до первого взятия")

        with container_lock(self.path):
            self.assertTrue(
                lp.exists(),
                "при взятии замка файл .lock должен быть создан",
            )

                                                                   
                                                             
                                 
        self.assertTrue(
            lp.exists(),
            "файл-замка не должно удаляться: он не мешает и создаёт гонку",
        )

    def test_lock_released_after_exit(self):
        pass
        with container_lock(self.path):
            pass

                                                                         
                                                   
        t0 = time.monotonic()
        with container_lock(self.path, timeout_s=TEST_TIMEOUT_S):
            pass
        dt = time.monotonic() - t0
        self.assertLess(
            dt, TEST_TIMEOUT_S,
            "замок не отпустился после выхода — второй захват ждал",
        )

    def test_reentrant_in_same_thread(self):
        pass





        with container_lock(self.path, timeout_s=TEST_TIMEOUT_S):
            with container_lock(self.path, timeout_s=TEST_TIMEOUT_S):
                with container_lock(self.path, timeout_s=TEST_TIMEOUT_S):
                    pass

    def test_reentrant_exit_does_not_release_early(self):
        pass






        acquired_by_other = []

        def try_other():
            try:
                with container_lock(self.path, timeout_s=TEST_TIMEOUT_S):
                    acquired_by_other.append(True)
            except ContainerLockBusy:
                acquired_by_other.append(False)

        with container_lock(self.path, timeout_s=TEST_TIMEOUT_S):
            with container_lock(self.path, timeout_s=TEST_TIMEOUT_S):
                                                                  
                                       
                t = threading.Thread(target=try_other, daemon=True)
                t.start()
                t.join(timeout=TEST_TIMEOUT_S * 2)

        self.assertEqual(
            acquired_by_other, [False],
            "чужой поток вошёл в замок, пока внешний with его держит — "
            "реентерабельность отпускает слишком рано",
        )

    def test_other_thread_blocked_while_held(self):
        pass





        holder_ready = threading.Event()
        release = threading.Event()
        got_busy = []

        def holder():
            with container_lock(self.path, timeout_s=TEST_TIMEOUT_S):
                holder_ready.set()
                release.wait(timeout=5.0)

        def second():
            holder_ready.wait(timeout=2.0)
            try:
                with container_lock(self.path, timeout_s=TEST_TIMEOUT_S):
                    got_busy.append(False)                 
            except ContainerLockBusy:
                got_busy.append(True)

        t1 = threading.Thread(target=holder, daemon=True)
        t2 = threading.Thread(target=second, daemon=True)
        try:
            t1.start()
            t2.start()
            t2.join(timeout=5.0)
        finally:
            release.set()
            t1.join(timeout=5.0)

        self.assertEqual(
            got_busy, [True],
            "второй поток вошёл в замок, пока первый его держит",
        )


                                                                             
                                          
                                                                             

class TestContainerIsLocked(_TmpContainer):
    def test_free_lock(self):
        pass
        self.assertFalse(container_is_locked(self.path))

    def test_held_lock(self):
        pass
        with container_lock(self.path, timeout_s=TEST_TIMEOUT_S):
            self.assertTrue(container_is_locked(self.path))

    def test_released_after_exit(self):
        pass
        with container_lock(self.path, timeout_s=TEST_TIMEOUT_S):
            pass
        self.assertFalse(
            container_is_locked(self.path),
            "замок числится занятым после выхода",
        )


                                                                             
                        
                                                                             

class TestUpdateContainer(_TmpContainer):
    def _seed(self):
        pass
        c = empty_container()
        w = add_work(c, "Docs", ["D:/a"], "D:/out.zpaq")
        save_container(self.path, c)
        return w["id"]

    def test_read_modify_write(self):
        pass




        self._seed()

        def mutate(c):
                                    
            add_work(c, "Photos", ["D:/p"], "D:/p.zpaq")

        result = update_container(self.path, mutate)

                                                     
        self.assertEqual(len(result.get("works") or []), 2)

                                                   
        on_disk = load_container(self.path)
        titles = [w.get("title") for w in on_disk.get("works") or []]
        self.assertIn("Photos", titles)
        self.assertIn("Docs", titles)

    def test_updates_metadata(self):
        pass





        c = empty_container()
        w = add_work(c, "Docs", ["D:/a"], "D:/out.zpaq")
        from core.tasks import add_job
        j = add_job(c, w["id"], {"title": "Daily"})
        save_container(self.path, c)

        def mutate(cc):
            update_job_meta(cc, j["id"], "busy")

        update_container(self.path, mutate)

        on_disk = load_container(self.path)
        from core.tasks import find_job
        found = find_job(on_disk, j["id"])
        self.assertIsNotNone(found)
        _work, job = found
        self.assertEqual(job["last_status"], "busy")
        self.assertEqual(job["run_count"], 1)

    def test_mutation_exception_does_not_write(self):
        pass




        work_id = self._seed()
        before = self.path.read_text(encoding="utf-8")

        def boom(c):
                                                              
            add_work(c, "Photos", ["D:/p"], "D:/p.zpaq")
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            update_container(self.path, boom)

        after = self.path.read_text(encoding="utf-8")
        self.assertEqual(
            after, before,
            "контейнер изменился, хотя мутация бросила исключение",
        )
                                    
        on_disk = load_container(self.path)
        self.assertEqual(len(on_disk.get("works") or []), 1)
        self.assertEqual(on_disk["works"][0]["id"], work_id)

    def test_lock_released_after_mutation_exception(self):
        pass





        self._seed()

        def boom(c):
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            update_container(self.path, boom)

                                               
        t0 = time.monotonic()
        update_container(self.path, lambda c: None)
        dt = time.monotonic() - t0
        self.assertLess(
            dt, DEFAULT_TIMEOUT_S,
            "замок не отпущен после исключения в мутации",
        )

    def test_busy_when_lock_held_by_other_thread(self):
        pass









        self._seed()
        holder_ready = threading.Event()
        release = threading.Event()

        def holder():
            with container_lock(self.path, timeout_s=5.0):
                holder_ready.set()
                release.wait(timeout=5.0)

        t = threading.Thread(target=holder, daemon=True)
        t.start()
        holder_ready.wait(timeout=2.0)

        caught = []
        try:
            update_container(self.path, lambda c: None)
        except ContainerLockBusy:
            caught.append(True)
        finally:
            release.set()
            t.join(timeout=5.0)

        self.assertEqual(
            caught, [True],
            "update_container не заметил, что замок занят другим потоком",
        )

    def test_reentrant_inside_existing_lock(self):
        pass






        self._seed()

        def inner_mutate(c):
            add_work(c, "Inner", ["D:/i"], "D:/i.zpaq")

        with container_lock(self.path, timeout_s=TEST_TIMEOUT_S):
            update_container(self.path, inner_mutate)

        on_disk = load_container(self.path)
        titles = [w.get("title") for w in on_disk.get("works") or []]
        self.assertIn("Inner", titles)


                                                                             
                          
                                                                             

class TestReExport(unittest.TestCase):
    pass







    def test_same_class(self):
        self.assertIs(ContainerLockBusy, TasksContainerLockBusy)


                                                                             
                  
                                                                             

class TestLockPath(_TmpContainer):
    def test_suffix(self):
        pass
        lp = lock_path_for(self.path)
        self.assertEqual(lp.name, CONTAINER_NAME + LOCK_SUFFIX)

    def test_next_to_container(self):
        pass
        lp = lock_path_for(self.path)
        self.assertEqual(lp.parent, self.path.parent)


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
    input("\nНажмите Enter для выхода...")
