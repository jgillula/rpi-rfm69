import sys
import math
from pylint.lint import Run

# Define thresholds: <3=red, <6=orange <9=yellow <10=green =10=brightgreen
thresholds = {3: 'red',
              6: 'orange',
              9: 'yellow',
              10: 'green',
              math.inf: 'brightgreen'}

results = Run(['--disable=import-error,unused-wildcard-import,wildcard-import', 'RFM69'], do_exit=False)
rating = results.linter.stats['global_note']
print("##[set-output name=rating]{:.2f}".format(rating))
for value in thresholds.keys():
    if rating < value:
        print("##[set-output name=color]{}".format(thresholds[value]))
        break
sys.exit(min(1, results.linter.stats["fatal"]
             + results.linter.stats["error"]
             + results.linter.stats["warning"]))
