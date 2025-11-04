from plyer import notification
import threading
import time
import datetime
import platform
import os
import database

notified_tasks = {}

def play_sound():
    try:
        if platform.system() == "Windows":
            import winsound
            winsound.Beep(1000, 700)
        elif platform.system() == "Darwin":
            os.system('say "Task Reminder"')
        else:
            if os.system("command -v play >/dev/null 2>&1") == 0:
                os.system('play -nq -t alsa synth 0.4 sine 440')
    except:
        pass

def check_reminders():
    global notified_tasks

    while True:
        try:
            rows = database.get_tasks(status_filter="Pending")
            now = datetime.datetime.now()
            current_time = now.strftime("%Y-%m-%d %H:%M")
            upcoming_time = (now + datetime.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M")

            for row in rows:
                task_id, task, remind_time, status, priority = row[:5]

                if remind_time <= current_time:
                    if task_id not in notified_tasks:
                        play_sound()

                        priority_emoji = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}.get(priority, '⚪')

                        notification.notify(
                            title=f"⏰ Task Reminder {priority_emoji}",
                            message=f"{task}\n\nDue: {remind_time}\nPriority: {priority}",
                            timeout=15,
                            app_name="To-Do Reminder"
                        )

                        notified_tasks[task_id] = current_time

                elif priority == "High" and remind_time == upcoming_time:
                    if f"upcoming_{task_id}" not in notified_tasks:
                        notification.notify(
                            title="📅 Upcoming Task",
                            message=f"{task}\n\nDue in 30 minutes",
                            timeout=10,
                            app_name="To-Do Reminder"
                        )
                        notified_tasks[f"upcoming_{task_id}"] = current_time

            if len(notified_tasks) > 1000:
                notified_tasks.clear()

        except:
            pass

        time.sleep(30)

def start_reminder_thread():
    t = threading.Thread(target=check_reminders, daemon=True)
    t.start()
