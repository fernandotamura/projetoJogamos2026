# screens/esportes.py
from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.clock import Clock
from components.checkbox_item import MDCheckboxItem


class ChooseSportsScreen(Screen):
    def on_pre_enter(self, *args):

        """
        Chamado antes da tela entrar.
        Aqui limpamos e repovoamos a lista de esportes.
        """
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

        # Garante que o id existe (caso o KV mude)        
        lista = getattr(self.ids, "lista_esportes", None)
        if not lista:
            App.get_running_app().toast("Erro: container 'lista_esportes' não encontrado.")
            return

        lista.clear_widgets()
        for nome, icone in esportes:
            lista.add_widget(MDCheckboxItem(text=nome, icon_path=icone))

        Clock.schedule_once(lambda *_: App.get_running_app().toast("Selecione pelo menos 3 esportes"), 0)

    def confirmar_escolhas(self):
        lista = getattr(self.ids, "lista_esportes", None)
        if not lista:
            App.get_running_app().toast("Erro: container 'lista_esportes' não encontrado.")
            return

        selecionados = []
        for item in lista.children:
            if hasattr(item, "active") and item.active:
                selecionados.append(item.text)

        if len(selecionados) < 3:
            App.get_running_app().toast("Escolha pelo menos 3 esportes")
        else:
            App.get_running_app().toast(f"Selecionados: {', '.join(selecionados)}")
            self.manager.current = "home"
