import pandas as pd
from pathlib import Path
from copy import deepcopy

# reuse logic from passive script
base = Path(__file__).with_name('run_scenario_C.py').read_text()
namespace = {'__file__': str(Path(__file__).with_name('run_scenario_C.py'))}

# This file will simply import the helper functions from the base script by exec
exec(base, namespace)

# override constants
# stake/loss overrides
namespace['WIN_PNL'] = 4
# Risk per full martingale cycle is doubled (4+8 stake), so loss per cycle is
# -$12 instead of the conservative -$6. Keep DAILY_GOAL in proportion (+$24).
namespace['LOSS_PNL'] = -12
# restore daily goal to 24
namespace['DAILY_GOAL'] = 24

if __name__ == '__main__':
    namespace['main']() 