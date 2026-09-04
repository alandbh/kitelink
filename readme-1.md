# O problema

Eu preciso usar o Google Drive no Linux em um computador de um usuário que não é muito familiarizado com terminal e não tem conhecimento tão avançado em tecnologia. Então eu tentei usar o pacote Rclone para mapear uma pasta no Nautilus, de modo que fosse transparente para esse usuário a experiência de interagir com os arquivos do Google Drive, assim como ele fazia na sua máquina Windows.

O problema em usar as soluções existentes para Linux é que elas não fazem a sincronização específica para arquivos, ou seja, geralmente eles baixam todos os arquivos para o armazenamento local. Mas eu precisava de uma solução muito parecida com a que já existe para o Google Drive Desktop no macOS e Windows, em que eu pudesse sincronizar apenas os arquivos específicos, ter uma visão de quais arquivos já foram sincronizados e quais ainda estão apenas na nuvem, também ter uma visualização de um arquivo no momento que ele está sendo sincronizado.

Por isso, como eu já conhecia o Rclone, eu pensei em montar uma pasta no Nautilus usando o Rclone como um serviço e aí o meu usuário não perceberia nenhuma ou quase nenhuma mudança na sua experiência com a gestão de arquivos do Google Drive.

O rclone tem funcionado relativamente bem para este propósito. No entanto, eu não consigo ter uma noção de quais arquivos estão sincronizados e quais ainda precisam ser sincronizados. Eu também não tenho uma noção de que um arquivo grande está sendo baixado quando eu dou um duplo clique nesse arquivo. Ou seja, se eu tiver um arquivo PDF de 70 megabytes, por exemplo, ao dar um duplo clique nesse arquivo, a interface fica em silêncio até que o leitor de PDF consiga abrir este arquivo.

A seguir, está o passo-a-passo que eu executei no meu Linux para usar o Rclone como uma pasta mapeada, apenas para você entender a solução alternativa que eu adotei até então.

No arquivo readme-2.md, você encontra mais detalhes sobre a aplicação que pretendo criar.

# Google Drive no Zorin OS com rclone + Nautilus

Guia completo de configuração do **rclone** no Zorin OS/Linux como substituto do Google Drive Desktop, com montagem automática no login e acesso pelo Nautilus (Files).

Esta configuração foi ajustada para priorizar **boa performance de navegação**, cache local e uso transparente no desktop.

---

## 1. Instalar o rclone

Primeiro, verifique se o rclone já está instalado:

```bash
rclone version
```

Se não estiver:

```bash
sudo apt update
sudo apt install rclone
```

Confirme novamente:

```bash
rclone version
```

---

## 2. Criar a pasta que será usada como ponto de montagem

```bash
mkdir -p "$HOME/Google Drive"
```

Essa pasta será exibida normalmente no Nautilus.

---

## 3. Configurar o Google Drive no rclone

Execute:

```bash
rclone config
```

Crie um novo remote e use, neste guia, o nome:

```text
gdrive
```

Escolha **Google Drive** como tipo de armazenamento.

### Usar Client ID e Client Secret próprios

Em vez de deixar `client_id` e `client_secret` vazios, informe credenciais OAuth próprias criadas em um projeto do Google Cloud com a Google Drive API habilitada.

Use placeholders como:

```text
client_id: <SEU_CLIENT_ID>
client_secret: <SEU_CLIENT_SECRET>
```

Não coloque credenciais reais neste arquivo.

O uso de um Client ID próprio evita depender do Client ID compartilhado historicamente pelo rclone e reduz a chance de throttling causado por quota compartilhada.

Para uso desktop normal, **não é necessário configurar uma Service Account**. A autenticação OAuth interativa com a conta Google do usuário é suficiente.

Quando perguntado se deseja usar o navegador para autenticação, escolha **Yes** em uma máquina com interface gráfica.

Faça login na conta Google desejada e autorize o acesso.

Para um My Drive normal, responda **No** quando o rclone perguntar se deseja configurar como Shared Drive/Team Drive.

---

## 4. Se você adicionou Client ID/Secret a um remote já existente

Edite o remote:

```bash
rclone config
```

Depois de salvar o novo `client_id` e `client_secret`, refaça a autorização OAuth:

```bash
rclone config reconnect gdrive:
```

Autorize novamente pelo navegador.

---

## 5. Testar o remote antes de montar

Confira os remotes:

```bash
rclone listremotes
```

Deve aparecer:

```text
gdrive:
```

Teste a raiz do Drive:

```bash
rclone lsd gdrive:
```

Se as pastas aparecerem, a autenticação está funcionando.

---

## 6. Criar o serviço systemd do usuário

Crie a pasta de serviços do usuário, se necessário:

```bash
mkdir -p ~/.config/systemd/user
```

Abra o arquivo:

```bash
nano ~/.config/systemd/user/rclone-google-drive.service
```

Cole:

```ini
[Unit]
Description=Google Drive (rclone)
Documentation=https://rclone.org/drive/ https://rclone.org/commands/rclone_mount/
After=default.target

[Service]
Type=simple
ExecStart=/usr/bin/rclone mount gdrive: "%h/Google Drive"     --config "%h/.config/rclone/rclone.conf"     --cache-dir "%h/.cache/rclone-google-drive"     --vfs-cache-mode full     --vfs-cache-max-size 10G     --vfs-cache-max-age 24h     --dir-cache-time 24h     --poll-interval 1m     --buffer-size 32M
ExecStop=/usr/bin/fusermount3 -uz "%h/Google Drive"
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

No nano, salve com:

```text
Ctrl+O
Enter
Ctrl+X
```

---

## 7. Por que essas opções melhoraram a performance

### `--vfs-cache-mode full`

Usa cache em disco para leitura e escrita e torna o mount muito mais compatível com aplicações que esperam um filesystem convencional.

### `--cache-dir "%h/.cache/rclone-google-drive"`

Mantém o cache deste mount em um diretório explícito.

### `--vfs-cache-max-size 10G`

Limita aproximadamente o cache VFS a 10 GB.

### `--vfs-cache-max-age 24h`

Permite remover do cache arquivos que não são acessados há 24 horas.

### `--dir-cache-time 24h`

Mantém a estrutura/listagem de diretórios em cache por bastante tempo, reduzindo consultas repetitivas ao Google Drive ao navegar pelo Nautilus.

### `--poll-interval 1m`

Permite que alterações externas no Google Drive sejam percebidas sem esperar o fim das 24 horas de cache de diretórios.

### `--buffer-size 32M`

Mantém um buffer de leitura em memória de tamanho moderado.

### Compatibilidade de `--vfs-refresh`

O rclone `v1.60.1` instalado nesta máquina não reconhece `--vfs-refresh`. Por isso, essa opção não é usada no serviço. As demais opções de cache e desempenho continuam ativas.

---

## 8. Ativar e iniciar automaticamente

Recarregue os arquivos do systemd:

```bash
systemctl --user daemon-reload
```

Habilite o serviço e inicie imediatamente:

```bash
systemctl --user enable --now rclone-google-drive.service
```

Confira:

```bash
systemctl --user status rclone-google-drive.service
```

O esperado é:

```text
active (running)
```

---

## 9. Confirmar a montagem

Teste:

```bash
ls "$HOME/Google Drive"
```

Também é possível verificar com:

```bash
mount | grep rclone
```

Depois, abra o Nautilus e navegue até:

```text
~/Google Drive
```

---

## 10. Adicionar aos favoritos do Nautilus

Abra `~/Google Drive` no Nautilus.

Adicione a pasta aos favoritos/bookmarks pela interface ou use, dependendo da versão:

```text
Ctrl+D
```

Assim, o Google Drive fica disponível diretamente na barra lateral.

---

## 11. Reiniciar o mount depois de alterar a configuração

Feche janelas do Nautilus que estejam usando a pasta `Google Drive` e execute:

```bash
systemctl --user daemon-reload
systemctl --user restart rclone-google-drive.service
```

Como o serviço já contém:

```ini
ExecStop=/usr/bin/fusermount3 -uz "%h/Google Drive"
```

normalmente não é necessário desmontar manualmente antes do restart.

---

## 12. Desmontagem manual

Se necessário:

```bash
fusermount3 -u "$HOME/Google Drive"
```

Se estiver ocupado, feche programas, terminais e janelas do Nautilus que estejam dentro dessa pasta.

Uma alternativa mais tolerante é:

```bash
fusermount3 -uz "$HOME/Google Drive"
```

---

## 13. Parar ou desativar o serviço

Parar temporariamente:

```bash
systemctl --user stop rclone-google-drive.service
```

Iniciar novamente:

```bash
systemctl --user start rclone-google-drive.service
```

Desabilitar a montagem automática:

```bash
systemctl --user disable --now rclone-google-drive.service
```

Reativar:

```bash
systemctl --user enable --now rclone-google-drive.service
```

---

## 14. Diagnóstico

Ver serviços rclone ativos:

```bash
systemctl --user list-units --type=service | grep -i rclone
```

Ver a configuração carregada:

```bash
systemctl --user cat rclone-google-drive.service
```

Ver status:

```bash
systemctl --user status rclone-google-drive.service
```

Ver logs recentes:

```bash
journalctl --user -u rclone-google-drive.service -n 100 --no-pager
```

Acompanhar logs ao vivo:

```bash
journalctl --user -u rclone-google-drive.service -f
```

Testar acesso direto à API sem o mount:

```bash
rclone lsd gdrive:
```

Ver qual arquivo de configuração o rclone usa:

```bash
rclone config file
```

> **Atenção:** o `rclone.conf` contém informações sensíveis, incluindo token OAuth. Não compartilhe seu conteúdo em tickets, chats ou documentos públicos.

---

## 15. Se o Nautilus estiver lento

Compare o acesso pelo filesystem:

```bash
time ls "$HOME/Google Drive"
```

com uma consulta direta ao rclone:

```bash
time rclone lsd gdrive:
```

Se ambos forem rápidos, mas o Nautilus continuar lento, o gargalo pode estar no próprio gerenciador de arquivos tentando obter thumbnails, tipos MIME e metadados adicionais.

Na primeira abertura após o login, o cache de diretórios ainda pode estar vazio. As navegações seguintes tendem a ser mais rápidas conforme as pastas são armazenadas no cache.

---

## 16. Problemas comuns

### `mountpoint is busy`

Feche qualquer programa usando `~/Google Drive` e tente:

```bash
fusermount3 -uz "$HOME/Google Drive"
systemctl --user restart rclone-google-drive.service
```

### Serviço não encontrado

Confira o nome:

```bash
systemctl --user list-units --type=service | grep -i rclone
```

Neste guia:

```text
rclone-google-drive.service
```

### Remote não encontrado

Confira:

```bash
rclone listremotes
```

Se `gdrive:` não aparecer:

```bash
rclone config
```

### Credenciais OAuth alteradas

Depois de trocar Client ID/Secret de um remote existente:

```bash
rclone config reconnect gdrive:
```

---

## 17. Configurando para outro usuário da mesma máquina

Faça toda a configuração logado no usuário que realmente utilizará o Google Drive.

Cada usuário terá seu próprio:

```text
~/.config/rclone/rclone.conf
~/.config/systemd/user/rclone-google-drive.service
~/Google Drive
~/.cache/rclone-google-drive
```

A autenticação OAuth deve ser feita com a conta Google daquele usuário.

Não copie tokens OAuth de uma conta para outra.

O mesmo OAuth Client ID/Client Secret pode ser reutilizado em mais de um remote, mas as credenciais e tokens devem permanecer privados.

---

## 18. Configuração final de referência

```text
Remote: gdrive:
Mountpoint: ~/Google Drive
Serviço: ~/.config/systemd/user/rclone-google-drive.service
Config rclone: ~/.config/rclone/rclone.conf
Cache: ~/.cache/rclone-google-drive
VFS cache: full
Máximo do cache: 10G
Idade do cache: 24h
Cache de diretórios: 24h
Polling: 1m
Buffer: 32M
Refresh inicial recursivo: desabilitado por incompatibilidade com rclone v1.60.1
Inicialização: systemd --user no login
```

---

## 19. Implementar notificações de transferência ao abrir arquivos grandes

Esta seção implementa um monitor local que acompanha as leituras do `rclone mount` e mostra o progresso no desktop. Siga todas as etapas na ordem apresentada.

Ao abrir pelo Nautilus um arquivo grande que ainda não está no cache local — por exemplo, um PDF de 70 MB — o `rclone mount` precisa buscar seus dados no Google Drive. Durante esse período, a janela pode parecer parada, mesmo que o download esteja ocorrendo normalmente.

Isso acontece porque o mount se apresenta ao Linux como um filesystem FUSE convencional. O Nautilus solicita a leitura do arquivo e aguarda a resposta, mas não recebe do FUSE/rclone uma porcentagem de download que possa exibir em sua própria interface. Portanto, não há uma forma direta de acrescentar uma barra de progresso nativa à janela do Nautilus apenas com uma opção do mount.

A solução tem duas partes:

1. habilitar o **Remote Control (RC)** no processo do `rclone mount`;
2. executar um monitor separado, como serviço do usuário, que consulte o RC e apresente notificações no desktop.

O fluxo será:

```text
Nautilus abre o arquivo
        │
        ▼
rclone mount inicia a leitura no Google Drive
        │
        ├── grava os dados no cache VFS
        │
        └── publica estatísticas pelo Remote Control
                         │
                         ▼
               monitor de transferências
                         │
                         ▼
        notificação no desktop com notify-send
```

### 19.1. Confirmar os pré-requisitos

Este tutorial pressupõe que:

- o mount `gdrive:` já funciona pelo Nautilus;
- o serviço `rclone-google-drive.service` está ativo;
- o Remote Control responde em `127.0.0.1:5572`.

Confira o serviço:

```bash
systemctl --user status rclone-google-drive.service --no-pager
```

Teste o RC:

```bash
rclone rc --url http://127.0.0.1:5572 core/stats
```

O comando deve retornar um objeto JSON. Se aparecer `connection refused`, revise primeiro a configuração do mount.

> **Compatibilidade:** no rclone `v1.60.1` usado neste guia, a opção `--vfs-refresh` não é reconhecida. Deixe essa opção fora do serviço. Isso não desativa o cache VFS nem o Remote Control.

### 19.2. Conferir o Remote Control no serviço do mount

No arquivo:

```text
~/.config/systemd/user/rclone-google-drive.service
```

o final do `ExecStart` deve conter:

```ini
    --buffer-size 32M \
    --rc \
    --rc-addr 127.0.0.1:5572
```

Todas as linhas têm uma barra `\` no final, exceto a última. Salve o arquivo e aplique a configuração:

```bash
systemctl --user daemon-reload
systemctl --user restart rclone-google-drive.service
```

Confirme que o serviço ficou ativo:

```bash
systemctl --user status rclone-google-drive.service --no-pager
```

Teste novamente:

```bash
rclone rc --url http://127.0.0.1:5572 core/stats
```

O endereço `127.0.0.1` restringe o RC à própria máquina. Não troque por `0.0.0.0`: a interface RC tem grande poder sobre o processo do rclone e não deve ser exposta à rede sem autenticação e proteção adequadas.

### 19.3. Instalar as dependências

O monitor usa apenas a biblioteca padrão do Python. O `notify-send` é fornecido pelo pacote `libnotify-bin`:

```bash
sudo apt update
sudo apt install python3 libnotify-bin
```

Teste uma notificação antes de continuar:

```bash
notify-send --app-name="Google Drive" "Teste do monitor" "As notificações estão funcionando."
```

Se a mensagem aparecer no desktop, prossiga.

### 19.4. Criar o programa do monitor

Crie a pasta de programas locais:

```bash
mkdir -p ~/.local/bin
```

Abra o arquivo:

```bash
nano ~/.local/bin/rclone-transfer-monitor
```

Cole o programa abaixo:

```python
#!/usr/bin/env python3
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

RC_STATS_URL = "http://127.0.0.1:5572/core/stats"
POLL_INTERVAL = 1
UPDATE_INTERVAL = 10


def format_bytes(value):
    value = max(float(value or 0), 0)
    units = ("B", "KB", "MB", "GB", "TB")
    unit = units[0]
    for unit in units:
        if value < 1024 or unit == units[-1]:
            break
        value /= 1024
    return f"{value:.1f} {unit}".replace(".", ",")


class TransferTracker:
    def __init__(self, update_interval=UPDATE_INTERVAL):
        self.update_interval = update_interval
        self.active = {}

    def update(self, transfers, now=None):
        now = time.monotonic() if now is None else now
        current = {item.get("name"): item for item in transfers if item.get("name")}
        events = []

        for name, item in current.items():
            previous = self.active.get(name)
            if previous is None or now - previous["last_notification"] >= self.update_interval:
                size = float(item.get("size") or 0)
                done = float(item.get("bytes") or 0)
                speed = float(item.get("speed") or 0)
                percentage = item.get("percentage")
                if percentage is None:
                    percentage = round(done * 100 / size) if size > 0 else 0
                percentage = max(0, min(100, int(percentage)))
                body = format_bytes(done)
                if size > 0:
                    body += f" de {format_bytes(size)}"
                if speed > 0:
                    body += f" — {format_bytes(speed)}/s"
                events.append({
                    "kind": "progress",
                    "name": name,
                    "body": body,
                    "percentage": percentage,
                })
                self.active[name] = {"last_notification": now}

        for name in list(self.active):
            if name not in current:
                events.append({
                    "kind": "complete",
                    "name": name,
                    "body": f"{Path(name).name} está pronto.",
                    "percentage": 100,
                })
                del self.active[name]

        return events


def fetch_transfers():
    request = urllib.request.Request(RC_STATS_URL, data=b"", method="POST")
    with urllib.request.urlopen(request, timeout=3) as response:
        payload = json.load(response)
    return payload.get("transferring") or []


def show_notification(event, notification_ids):
    name = event["name"]
    display_name = Path(name).name
    command = [
        "notify-send",
        "--print-id",
        "--app-name=Google Drive",
        "--icon=folder-remote",
        "--urgency=normal",
        "--expire-time=5000",
        f"--hint=int:value:{event['percentage']}",
    ]
    if name in notification_ids:
        command.append(f"--replace-id={notification_ids[name]}")
    title = f"Baixando {display_name}" if event["kind"] == "progress" else "Google Drive"
    result = subprocess.run(
        command + [title, event["body"]],
        check=True,
        capture_output=True,
        text=True,
    )
    notification_id = result.stdout.strip()
    if notification_id:
        notification_ids[name] = notification_id
    if event["kind"] == "complete":
        notification_ids.pop(name, None)


def main():
    tracker = TransferTracker()
    notification_ids = {}
    warned = False

    while True:
        try:
            transfers = fetch_transfers()
            warned = False
            for event in tracker.update(transfers):
                show_notification(event, notification_ids)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            if not warned:
                print(f"RC indisponível: {error}", flush=True)
                warned = True
        except subprocess.CalledProcessError as error:
            print(f"Falha ao exibir notificação: {error.stderr.strip()}", flush=True)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
```

Salve no nano com `Ctrl+O`, `Enter` e `Ctrl+X`. Depois torne o programa executável:

```bash
chmod +x ~/.local/bin/rclone-transfer-monitor
```

O monitor consulta o RC a cada segundo, mas atualiza a notificação de cada arquivo no máximo uma vez a cada dez segundos. As atualizações reutilizam a mesma notificação para reduzir o excesso de mensagens. A urgência `normal` é necessária porque o Zorin/GNOME pode registrar notificações de urgência `low` sem exibir o banner na tela.

### 19.5. Testar o monitor manualmente

Execute:

```bash
~/.local/bin/rclone-transfer-monitor
```

Deixe o terminal aberto e, no Nautilus, abra um arquivo grande que ainda não esteja no cache local. Deve aparecer uma notificação com nome, quantidade transferida, tamanho total e velocidade. Quando a transferência sair da lista do rclone, a notificação será atualizada para informar que o arquivo está pronto.

Encerre o teste com `Ctrl+C`.

> **Observação:** um arquivo já presente no cache pode abrir imediatamente e não gerar transferência nem notificação. Para um teste confiável, use um arquivo grande que ainda não tenha sido aberto nesta máquina.

### 19.6. Executar o monitor como serviço do usuário

Crie o arquivo do serviço:

```bash
nano ~/.config/systemd/user/rclone-transfer-monitor.service
```

Cole:

```ini
[Unit]
Description=Notificações de transferência do Google Drive
After=rclone-google-drive.service graphical-session.target
Requires=rclone-google-drive.service

[Service]
Type=simple
ExecStart=%h/.local/bin/rclone-transfer-monitor
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

Salve com `Ctrl+O`, `Enter` e `Ctrl+X`. Recarregue os serviços e ative o monitor:

```bash
systemctl --user daemon-reload
systemctl --user enable --now rclone-transfer-monitor.service
```

Confira:

```bash
systemctl --user status rclone-transfer-monitor.service --no-pager
```

O esperado é `active (running)`.

### 19.7. Fazer o teste final

1. Confirme que os dois serviços estão ativos:

    ```bash
    systemctl --user is-active rclone-google-drive.service
    systemctl --user is-active rclone-transfer-monitor.service
    ```

2. Abra pelo Nautilus um arquivo grande que não esteja no cache.
3. Observe a notificação de progresso.
4. Aguarde a mensagem de conclusão.

Enquanto o arquivo estiver sendo transferido, também é possível conferir os dados brutos em outro terminal:

```bash
rclone rc --url http://127.0.0.1:5572 core/stats
```

### 19.8. Diagnóstico do monitor

Ver os logs recentes:

```bash
journalctl --user -u rclone-transfer-monitor.service -n 50 --no-pager
```

Acompanhar ao vivo:

```bash
journalctl --user -u rclone-transfer-monitor.service -f
```

Se o comando de reinicialização mostrar:

```text
Unit rclone-transfer-monitor.service not found
```

isso significa que a execução manual do programa funcionou, mas a unidade systemd ainda não foi criada ou carregada. Conclua primeiro a seção 19.6. Se o arquivo do serviço já existir, carregue-o e ative-o:

```bash
systemctl --user daemon-reload
systemctl --user enable --now rclone-transfer-monitor.service
```

Confira se o systemd reconhece a unidade:

```bash
systemctl --user status rclone-transfer-monitor.service --no-pager
```

Somente depois que a unidade existir e estiver carregada, use o comando de reinicialização após alterar o programa:

```bash
systemctl --user restart rclone-transfer-monitor.service
```

Se aparecer `RC indisponível`, confirme primeiro:

```bash
systemctl --user status rclone-google-drive.service --no-pager
rclone rc --url http://127.0.0.1:5572 core/stats
```

Se `notify-send` funcionar no terminal, mas não pelo serviço, confira se o monitor foi iniciado dentro da sessão gráfica do mesmo usuário que executa o Nautilus.

Parar temporariamente:

```bash
systemctl --user stop rclone-transfer-monitor.service
```

Desativar completamente:

```bash
systemctl --user disable --now rclone-transfer-monitor.service
```

### 19.9. Limitações conhecidas

- O Nautilus continua sem receber progresso diretamente; a indicação aparece como notificação separada.
- Arquivos já armazenados no cache local não geram nova transferência.
- Transferências muito rápidas podem terminar antes da primeira atualização visível.
- O monitor considera que uma transferência terminou quando ela desaparece da lista `transferring` do RC. Se uma aplicação cancelar a leitura, a mensagem final ainda poderá dizer que o arquivo está pronto.
- O formato dos dados do RC pode mudar entre versões do rclone. Se uma atualização quebrar o monitor, consulte os logs e o retorno de `core/stats`.

### 19.10. Evolução opcional: ícone ou indicador na bandeja

Uma evolução posterior seria substituir ou complementar as notificações com um pequeno indicador residente na área de status do desktop. Ele poderia mostrar estados como:

- Google Drive montado e ocioso;
- arquivo sendo baixado;
- velocidade atual e quantidade de transferências;
- transferência concluída;
- mount desconectado ou com erro.

Ao clicar no ícone, poderia aparecer uma lista compacta das transferências em andamento. Essa solução evita várias notificações, mas exige uma aplicação gráfica, integração com o ambiente GNOME/Zorin e possivelmente uma extensão compatível com indicadores de aplicativos. Por isso, é melhor tratá-la como uma segunda etapa, depois que o monitor básico via `notify-send` estiver estável.

## 20. Problemas com a abordagem do item 19 (serviço de notificações)

Tive que desinstalar o serviço de monitoramento do rclone porque ele inundou a minha área de trabalho com um monte de notificações. Toda vez que eu entrava numa pasta ele aparecia uma notificação para cada arquivo dentro dessa pasta. Então eu achei melhor desabilitar porque poluiu demais a interface aqui do sistema operacional.

É que o monitor atual trata qualquer item presente em `core/stats → transferring` como um arquivo aberto pelo usuário. Mas o Nautilus também lê arquivos automaticamente para gerar miniaturas, identificar tipos MIME, calcular metadados e preencher a pasta. O rclone registra essas leituras, e o monitor não consegue distinguir automaticamente um duplo clique dessas operações em segundo plano.

Por isso ele gerou uma notificação por arquivo. A solução precisa ser redesenhada antes de ser reativada. Eu recomendaria:

- não notificar imediatamente;
- ignorar transferências menores que, por exemplo, 20 ou 50 MB;
- só avisar se a transferência continuar por mais de 3–5 segundos;
- usar uma única notificação agregada, em vez de uma por arquivo;
- atualizar essa mesma notificação com algo como “3 arquivos sendo transferidos”;
- evitar mensagem de conclusão para leituras rápidas ou incompletas.

Até implementarmos esses filtros, manter o serviço desabilitado é a melhor escolha:

```bash
systemctl --user disable --now rclone-transfer-monitor.service
```

O mount e as otimizações do rclone continuam funcionando normalmente; somente as notificações ficam desativadas. O tutorial atual também deveria ser corrigido, pois a implementação nele é funcional, mas inadequada para o comportamento real do Nautilus.

### 20.1 Desistência

Resolvi abandonar a estratégia da notificação do item 19.

## Referências oficiais

- rclone Google Drive: https://rclone.org/drive/
- rclone mount / VFS: https://rclone.org/commands/rclone_mount/
- rclone Remote Control / API: https://rclone.org/rc/
- comando `rclone rc`: https://rclone.org/commands/rclone_rc/

---

## Nota

Este guia registra a configuração que funcionou bem no Zorin OS em agosto de 2026. Como rclone, Google OAuth e Google Drive API evoluem, vale consultar a documentação oficial ao repetir o procedimento no futuro.
