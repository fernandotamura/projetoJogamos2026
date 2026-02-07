from kivymd.uix.screen import MDScreen


class AppShellScreen(MDScreen):
    """
    Área logada do app: contém TopAppBar + NavigationDrawer + páginas internas.
    """

    def open_drawer(self):
        self.ids.nav_drawer.set_state("open")

    def close_drawer(self):
        self.ids.nav_drawer.set_state("close")

    def go_to(self, screen_name: str):
        """
        Troca a página interna do Shell (ex.: dashboard, favorites).
        """
        self.ids.shell_sm.current = screen_name
        self.close_drawer()