import os

# The repo dir in which Groupy runs a callback, whatever the cwd of Claude is
GROUPY_REPO_DIR = os.environ.get("GROUPY_REPO_DIR", "")

# The dir of the Claude request that runs a callback (set by the Claude
# policies for the claude process, and inherited by groupy callback)
GROUPY_REQUEST_DIR = os.environ.get("GROUPY_REQUEST_DIR", "")

# Whether the callbacks run in an RFR
GROUPY_IN_RFR = os.environ.get("GROUPY_IN_RFR", "") == "1"
