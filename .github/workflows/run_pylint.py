import sys
from glob import glob
from pylint.lint import Run
import pylint

print("Running pylint version {}".format(pylint.__version__))

# Define thresholds: <3=red, <6=orange <8=yellow <9.5=green <10=brightgreen
thresholds = {3: 'red',
              6: 'orange',
              8: 'yellow',
              9.5: 'green',
              10: 'brightgreen'}

results = Run(['--disable=import-error,unused-wildcard-import,wildcard-import,line-too-long,invalid-name,missing-module-docstring,too-many-lines,too-many-instance-attributes,consider-using-f-string,too-many-locals,too-few-public-methods,too-many-branches,duplicate-code,too-many-public-methods', 'RFM69'] + glob("tests/*.py") + glob("examples/*.py"), exit=False)

if results.linter.stats.fatal + results.linter.stats.error + results.linter.stats.warning > 0:
    print("rating=failing!")
    print("color=red")
    print("linting_status=failed")
else:
    rating = results.linter.stats.global_note
    print("rating={:.2f}".format(rating))
    for value in thresholds.keys():
        if rating <= value:
            print("color={}".format(thresholds[value]))
            break
    print("linting_status=passed")
sys.exit(0)
