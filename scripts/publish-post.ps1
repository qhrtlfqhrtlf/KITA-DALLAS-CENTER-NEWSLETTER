$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$ScriptDir\publish_post.py"
