# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors:     you (you@yourinstitution.email)
# *
# * your institution
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'you@yourinstitution.email'
# *
# **************************************************************************
from pyworkflow.gui import ListTreeProviderString
from pyworkflow.object import String
import pyworkflow.gui.dialog as dialog

from deepfinder.protocols import DeepFinderPrefixHelloWorld
from pyworkflow.wizard import Wizard


class DeepFinderPrefixHelloWorldWizard(Wizard):
    # Dictionary to target protocol parameters
    _targets = [(DeepFinderPrefixHelloWorld, ['message'])]

    def show(self, form, *params):

        # This are the greetings:
        greetings = [String("Hello world"), String("Hola mundo"),
                     String("Bonjour le monde"), String("Hallo Welt"),
                     String("Kon'nichiwa sekai"), String("Nǐ hǎo, shìjiè"),
                     String("Ciao mondo"), String("Hallo Wereld"),
                     String("Privet, mir")]

        # Get a data provider from the greetings to be used in the tree (dialog)
        provider = ListTreeProviderString(greetings)

        # Show the dialog
        dlg = dialog.ListDialog(form.root, "Greetings from the world", provider,
                                "Select one of the greetings)")

        # Set the chosen value back to the form
        form.setVar('message', dlg.values[0].get())
