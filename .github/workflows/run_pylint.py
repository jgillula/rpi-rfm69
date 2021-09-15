import sys
from pylint.lint import Run
import anybadge

# Define thresholds: <2=red, <4=orange <8=yellow <10=green
thresholds = {2: 'red',
              4: 'orange',
              6: 'yellow',
              10: 'green'}

results = Run(['--disable=import-error,unused-wildcard-import,wildcard-import', 'RFM69'], do_exit=False)
# `exit` is deprecated, use `do_exit` instead
badge = anybadge.Badge('pylint', round(results.linter.stats['global_note'], 2), thresholds=thresholds)
badge.write_badge('pylint.svg')
sys.exit(min(1, results.linter.stats["fatal"]
             + results.linter.stats["error"]
             + results.linter.stats["warning"]))
