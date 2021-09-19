import sys
import math
from glob import glob
from pylint.lint import Run

# Define thresholds: <3=red, <6=orange <9=yellow <10=green =10=brightgreen
thresholds = {3: 'red',
              6: 'orange',
              9: 'yellow',
              10: 'green',
              math.inf: 'brightgreen'}

results = Run(['--disable=import-error,unused-wildcard-import,wildcard-import,line-too-long,invalid-name,missing-module-docstring,too-many-lines,too-many-instance-attributes,consider-using-f-string,too-many-locals,too-few-public-methods,too-many-branches,duplicate-code', 'RFM69'] + glob("tests/*.py") + glob("examples/*.py"), do_exit=False)

if results.linter.stats["fatal"] + results.linter.stats["error"] + results.linter.stats["warning"] > 0:
    print("##[set-output name=rating]failing!")
    print("##[set-output name=color]red")
else:
    rating = results.linter.stats['global_note']
    print("##[set-output name=rating]{:.2f}".format(rating))
    for value in thresholds.keys():
        if rating < value:
            print("##[set-output name=color]{}".format(thresholds[value]))
            break
sys.exit(0)
