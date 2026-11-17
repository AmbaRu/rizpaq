


from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCALES = ROOT / 'locales'

KEYS = [
    'tip.create_archive',
    'tip.open_archive',
    'tip.refresh',
    'tip.latest_only',
    'tip.archive_info',
    'tip.compare_versions',
    'tip.extract_file',
    'tip.extract_folder',
    'tip.extract_all_versions',
    'tip.extract_until',
    'tip.extract_to',
    'tip.extract_force',
    'tip.salvage',
    'tip.compression',
    'tip.hash_algorithm',
    'tip.only_masks',
    'tip.not_masks',
    'tip.password',
    'tip.comment',
    'tip.longpath',
    'tip.norecursion',
    'tip.forcewindows',
    'tip.nochecksum',
    'tip.nodedup',
    'tip.verify',
    'tip.test_archive',
    'tip.verify_fs',
    'tip.sync',
    'tip.paranoid',
    'tip.second_copy',
    'tip.par2_create',
    'tip.par2_verify',
    'tip.par2_repair',
    'tip.par2_redundancy',
    'tip.schedule_enable',
    'tip.schedule_skip_unchanged',
    'tip.schedule_continuous',
    'tip.dashboard',
    'tip.catalog',
    'tip.global_search',
    'tip.language',
    'tip.skin',
    'tip.engine_path',
    'tip.notify',
    'tip.tasks_dir',
    'tip.associations',
    'tip.updates',
    'tip.manual',
    'tip.command_ref',
    'tip.cancel',
    'tip.open_external',
]


class TestTooltipLocales(unittest.TestCase):
    def test_all_keys_in_all_languages(self):
        for path in sorted(LOCALES.glob('*.json')):
            data = json.loads(path.read_text(encoding='utf-8'))
            strings = data['strings']
            missing = [k for k in KEYS if k not in strings]
            empty = [k for k in KEYS if not strings.get(k)]
            self.assertEqual(missing, [], '%s: missing %s' % (path.name, missing))
            self.assertEqual(empty, [], '%s: empty %s' % (path.name, empty))

    def test_tooltips_are_used_in_ui(self):
        used = set()
        for path in (ROOT / 'ui').glob('*.py'):
            text = path.read_text(encoding='utf-8')
            for key in KEYS:
                if 'tr("%s")' % key in text or "tr('%s')" % key in text:
                    used.add(key)
        self.assertGreaterEqual(len(used), 25, 'too few tooltips wired: %d' % len(used))


if __name__ == '__main__':
    unittest.main()
