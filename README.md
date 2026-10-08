# Markov-chain-MIDI

Script em Python que utiliza o algoritmo de Cadeias de Markov para analisar arquivos MIDI e gerar novas composições baseadas nos padrões aprendidos. O código foi baseado nessa outra implementação disponivel em: https://github.com/onurmatik/MarkovMusic/blob/main/markov_music.py

## Utilização

1. (Opcional) Crie e ative um ambiente virtual;
2. Instale as dependências necessárias utilizando o arquivo requirements.txt:

~~~sh
pip install -r requirements.txt
~~~

Para gerar uma música baseada em um único arquivo MIDI ou uma pasta:
~~~sh
python generate.py seuMIDIfile.mid
python generate.py suaPasta/*.mid
~~~

#### Argumentos Disponíveis

  files (Obrigatório): Caminhos para os arquivos MIDI de entrada.

  -o, --order (Opcional): Ordem da cadeia de Markov. (Padrão: 3)

  -of, --output-file (Opcional): Nome do arquivo MIDI de saída. (Padrão: output.mid)

  -n, --max-notes (Opcional): Número máximo de notas a serem geradas. (Padrão: 150)

  -s, --seed (Opcional): Define uma semente (seed) para o gerador aleatório.

  -v, --visualize (Opcional): Abre uma janela interativa mostrando o grafo com as transições de notas mais frequentes da Cadeia de Markov.

## Reproduzir Resultados
Ex1:
~~~sh
python generate.py pastaComODataset/*.mid -s 865 -o 5
~~~
Ex2:
~~~sh
python generate.py pastaComODataset/*.mid -s 500
~~~

Os outros exemplos foram gerados com seeds desconhecidas.

## Uso de IA
IA foi usada para fazer a função de vizualização da cadeia de Markov (vizualize_chain), e para auxiliar no refinamento dos resultados. Esse refinamento inclui a quantização das notas para que notas com pequnas variações de duração sejam consideradas iguas durante a extração e a prevenção de uma única nota se repetir ou duas ficarem oscilando indefinidamente durante a geração.
