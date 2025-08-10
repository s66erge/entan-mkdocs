# specify the path to the folder you want to monitor:
$Path = '.\'

# specify which files you want to monitor
$FileFilter1 = "*.*"  # the filter is done on the CHANGED files below

# specify whether you want to monitor subfolders as well:
$IncludeSubfolders = $true

# specify the file or folder properties you want to monitor:
$AttributeFilter = [IO.NotifyFilters]::FileName, [IO.NotifyFilters]::LastWrite 

# specify the type of changes you want to monitor:
$ChangeTypes = [System.IO.WatcherChangeTypes]::All, [System.IO.WatcherChangeTypes]::Deleted

# specify the maximum time (in milliseconds) you want to wait for changes:
$Timeout = 500

# define a function that gets called for every change:
function Invoke-SomeAction
{
  param
  (
    [Parameter(Mandatory)]
    [System.IO.WaitForChangedResult]
    $ChangeInformation
  )

# Check if the file name either :
# - starts with 'docs\' and ends with .md
# - is the main.py file
  if ($ChangeInformation.Name -match '^(docs\\.*\.md|main\.py)$') {

    Write-Warning 'Change detected:' 
    $ChangeInformation.Name | Out-String | Write-Host -ForegroundColor DarkYellow
  
    # run entangled sync command
    entangled sync
  }
}
  # use a try...finally construct to release the
# filesystemwatcher once the loop is aborted
# by pressing CTRL+C

try
{
  Write-Warning "FileSystemWatcher is monitoring $Path"
  
  # create a filesystemwatcher object
  $watcher = New-Object -TypeName IO.FileSystemWatcher -ArgumentList $Path, $FileFilter1 -Property @{
    IncludeSubdirectories = $IncludeSubfolders
    NotifyFilter = $AttributeFilter}
  
  # start monitoring manually in a loop:
  do
  {
    # wait for changes for the specified timeout
    # IMPORTANT: while the watcher is active, PowerShell cannot be stopped
    # so it is recommended to use a timeout of 1000ms and repeat the
    # monitoring in a loop. This way, you have the chance to abort the
    # script every second.
    $result = $watcher.WaitForChanged($ChangeTypes, $Timeout)
    # if there was a timeout, continue monitoring:
    if ($result.TimedOut) { continue }

    Invoke-SomeAction -Change $result
    
    # the loop runs forever until you hit CTRL+C    
  } while ($true)
}
finally
{
  # release the watcher and free its memory:
  $watcher.Dispose()
  Write-Warning 'FileSystemWatcher removed.'
}