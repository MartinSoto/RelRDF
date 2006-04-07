import re

import gtk

import kiwi.ui.delegates
import kiwi.ui.views

class UiManagerSignalBroker(object):
    def _do_connections(self, view, methods):
        self._autoconnectUiManager(view, methods)
        super(UiManagerSignalBroker, self)._do_connections(view, methods)

    def _autoconnectUiManager(self, view, methods):
        for group in  view.uiManager.get_action_groups():
            for action in group.list_actions():
                methodName = 'on_%s__activate' % action.get_name()
                method = getattr(view, methodName)
                action.connect('activate', method)
                del methods[methodName]


class SignalBroker(UiManagerSignalBroker,
                   kiwi.ui.views.SignalBroker):
    pass

class GladeSignalBroker(UiManagerSignalBroker,
                        kiwi.ui.views.GladeSignalBroker):
    pass


class UiManagerSlaveView(object):
    """A view extension that adds a GTK UIManager and configures and
    connects it automatically based on object/class attibutes."""

    _actionRegex = re.compile(r'^(\w+)__actions$')

    def __init__(self, *args, **kwargs):
        self.uiManager = gtk.UIManager()

        # Create actions and action groups.
        # FIXME: Do not rely on dir for doing this.
        for name in dir(self):
            match = self._actionRegex.match(name)
            if match is not None:
                groupName, = match.groups()
                actionGroup = gtk.ActionGroup(groupName)
                actionGroup.add_actions(getattr(self, name))
                self.uiManager.insert_action_group(actionGroup, 0)

        super(UiManagerSlaveView, self).__init__(*args, **kwargs)

        # Add UI definitions to the UIManager.
        if hasattr(self, 'uiDefinition'):
            self.uiManager.add_ui_from_string(self.uiDefinition)

    def _attach_callbacks(self, controller):
        if self._glade_adaptor is None:
            brokerclass = SignalBroker
        else:
            brokerclass = GladeSignalBroker

        self._broker = brokerclass(self, controller)


class UiManagerDelegate(UiManagerSlaveView, kiwi.ui.delegates.Delegate):
    pass

class UiManagerSlaveDelegate(UiManagerSlaveView,
                             kiwi.ui.delegates.SlaveDelegate):
    pass

