import json
from pprint import pprint

_OPTIONS = '''
{
  "categories": [
    {
      "category": "Identification and Command",
      "properties": [
        {
          "name": "name",
          "description": "Unique identifier for the task (used for logs, dependencies, and notifications)."
        },
        {
          "name": "command",
          "description": "The actual system command to be executed."
        },
        {
          "name": "user",
          "description": "The Unix username under which the command will be launched (for permission control)."
        },
        {
          "name": "where",
          "description": "The working directory from which the command will be executed."
        }
      ]
    },
    {
      "category": "Scheduling and Recurrence",
      "properties": [
        {
          "name": "schedule-cron",
          "description": "Defines recurrence using standard Cron syntax (e.g., '0 0 * * *')."
        },
        {
          "name": "timer",
          "description": "Fixed time interval for task repetition (e.g., '30s', '5m'). Use 'none' if 'schedule-cron' is used."
        },
        {
          "name": "timeout",
          "description": "Maximum time allowed for task execution. If exceeded, the process is terminated."
        }
      ]
    },
    {
      "category": "Failure Control and Dependencies",
      "properties": [
        {
          "name": "times",
          "description": "Maximum number of times the script will be attempted (including the first attempt)."
        },
        {
          "name": "on-fail",
          "description": "Behavior if the task fails: 'stop' (cease attempts) or 'restart' (retry)."
        },
        {
          "name": "depends-on",
          "description": "List of task names that must have successfully completed before this one starts."
        },
        {
          "name": "success-codes",
          "description": "List of exit codes that should be considered successful, in addition to the standard 0."
        }
      ]
    },
    {
      "category": "Resources and Environment",
      "properties": [
        {
          "name": "environment-file",
          "description": "Path to a JSON file containing the environment variables to be injected into the execution."
        },
        {
          "name": "priority",
          "description": "Process priority ('nice' value). A lower number indicates higher CPU priority."
        }
      ]
    },
    {
      "category": "Logging and Notification",
      "properties": [
        {
          "name": "stdout",
          "description": "Path to redirect the command's standard output."
        },
        {
          "name": "stderr",
          "description": "Handling of error output: 'combined', 'separate', or a specific file path."
        },
        {
          "name": "notify",
          "description": "Condition for sending a notification (e.g., Unix mail): 'none', 'on-fail', 'all'."
        }
      ]
    }
  ]
}
'''

def print_help(data):

    categories = data.get("categories", [])
    category = 1
    for cat in categories:
        print(f"{category}. {cat['category']}:")
        for property in cat.get('properties', []):
            name = property['name']
            description = property['description']
            #short_description = description.split('.')[0]
            print(f"    - {name}: {description}...")
        print()
        category += 1


