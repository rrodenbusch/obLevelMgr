# A simple utility to help manage Elder Scrolls Oblivion Leveling
#
# (C) Copyright Richard Rodenbusch 2023.
#
# This code is licensed under the GNU Affero General Public License v3.0
# You may obtain a copy of this license in the LICENSE file in the root directory
# of this source tree or at https://www.gnu.org/licenses/agpl-3.0.en.html .
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# pylint: disable=bad-docstring-quotes,invalid-name
__version__="0.1.0"

import tkinter as tk

from .datadialogs import (LocalDataFrame,
                          LocalButtonFrame,
                          LocalTableDialog,
                          SideBySideDialog,
                          LocalEntryFrame,
                          LocalEntryDialog,
                          askinteger,
                          askstring,)