from kivy.uix.screenmanager import Screen
from kivymd.toast import toast
from components.checkbox_item import MDCheckboxItem

class EsportesScreen(Screen):
    def on_enter(self):
        esportes = [
            ("Futebol", "assets/icons/futebol.png"),
            ("Vôlei", "assets/icons/volei.png"),
            ("Basquete", "assets/icons/basquete.png"),
            ("Tênis", "assets/icons/tenis.png"),
            ("Natação", "assets/icons/natacao.png"),
            ("Corrida", "assets/icons/corrida.png"),
            ("Caminhada", "assets/icons/caminhada.png"),
            ("Skate", "assets/icons/skate.png"),
            ("BMX", "assets/icons/bmx.png"),
            ("Badminton", "assets/icons/badminton.png"),
            ("Jiu-Jitsu", "assets/icons/jiujitsu.png"),
            ("Judô", "assets/icons/judo.png"),
            ("Karatê", "assets/icons/karate.png"),
            ("Boxe", "assets/icons/boxe.png"),
            ("Muay Thai", "assets/icons/muaythai.png"),
            ("Yoga", "assets/icons/yoga.png"),
            ("Pilates", "assets/icons/pilates.png"),
            ("Crossfit", "assets/icons/crossfit.png"),
            ("Ciclismo", "assets/icons/ciclismo.png"),
            ("Surf", "assets/icons/surf.png"),
            ("Escalada", "assets/icons/escalada.png"),
            ("Rugby", "assets/icons/rugby.png"),
            ("Beisebol", "assets/icons/beisebol.png"),
            ("Handebol", "assets/icons/handebol.png"),
            ("Tênis de mesa", "assets/icons/tenisdemesa.png"),
            ("Golfe", "assets/icons/golfe.png"),
            ("Hóquei", "assets/icons/hoquei.png"),
            ("Esgrima", "assets/icons/esgrima.png"),
        ]
        self.ids.lista_esportes.clear_widgets()
        for nome, icone in esportes:
            self.ids.lista_esportes.add_widget(MDCheckboxItem(text=nome, icon_path=icone))

    def confirmar_escolhas(self):
        selecionados = []
        for item in self.ids.lista_esportes.children:
            if hasattr(item, 'active') and item.active:
                selecionados.append(item.text)
        if len(selecionados) < 3:
            toast("Escolha pelo menos 3 esportes")
        else:
            toast(f"Selecionados: {', '.join(selecionados)}")
            self.manager.current = "home"

