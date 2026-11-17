






from __future__ import annotations

from PySide6.QtWidgets import QMessageBox

from ui.i18n import tr


def confirm_schedule_conflicts(parent, container, work, job, schedule) -> bool:
    pass
    if not schedule or not schedule.get("enabled"):
        return True
    if not container or not work or not job:
        return True

    try:
        from core.schedule_conflicts import find_conflicts

        conflicts = find_conflicts(container, work, job, schedule)
    except Exception:
                                                                                   
                                                    
        return True

    if not conflicts:
        return True

    items = "\n".join(
        tr(
            "scheduler.conflict_item",
            work=c.get("work") or "?",
            job=c.get("job") or "?",
        )
        for c in conflicts
    )
    answer = QMessageBox.question(
        parent,
        tr("scheduler.conflict_title"),
        tr("scheduler.conflict_text", items=items),
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    return answer == QMessageBox.Yes
