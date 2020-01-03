# Set it up to run every second hour.

# See https://www.reddit.com/r/PowerShell/comments/8vjpzq/registerscheduledtask_using_daily_and_repetition/e1nwghk/

$a = New-ScheduledTaskAction -Execute "C:\cyboko\sync.bat"
$tr = New-ScheduledTaskTrigger -Daily -At '00:30'
$t = Register-ScheduledTask -TaskName "CYB Ajour Sync" -Trigger $tr -Action $a
$t.Triggers.Repetition.Duration = 'P7300D'
$t.Triggers.Repetition.Interval = 'PT120M'
$t | Set-ScheduledTask
