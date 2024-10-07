# Importando todas as bibliotecas necessárias

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime

#---------------------------------------------------------------------------------------------------------
#                                       FUNÇÕES
#---------------------------------------------------------------------------------------------------------
def ler_arquivo(caminho):

  df = pd.read_csv(caminho) #realiza a leitura do arquivo csv
  df1 = df.copy() #faz uma cópia do dataframe, importante para trabalhar mantendo o dataframe inicial se necessário alguma comparação posteriormente.

  return df1

def printar_colunas(df):

  """ Definindo as colunas com .columns() e transformando em
      uma lista para facilitar a vizualização ao printar. """
  colunas = df.columns.to_list()

  print("As colunas do Dataset são: \n")

  # No loop vamos printar as colunas uma """
  for col in colunas:

      print(f"- {col};")

def filmes_cadastrados(df):


  linhas = df['show_id'].isna() == False

  df = df.loc[linhas,:]

  print(f'\nO número de filmes estão disponíveis na Netflix é de {len(df)} filmes.\n')
  return (len(df))

def top_5_diretores(df):

  """ Primeiro verifiquei que algumas obras tinham mais de um diretor, ou seja,
  apenas um groupby() não resolveria, pois teriamos filmes dirigidos por mais pessoas
  que não contariam para o número individual do diretor. O maior exemplo é que realizando isso
  teriamos Jan Suter, Raúl Campos com 18 obras dirigidas, mas sem considerar suas obras solo.

  Com isso, a escolha foi utilizar o explode para criar uma linha para cada vez que o diretor é mencionado.
  Sendo diretor solo ou com mais diretores."""

  obras_dirigidas = df['director'].str.split(',').explode().str.strip()


  contagem_obras = obras_dirigidas.value_counts().reset_index()


  # renomeando as colunas
  contagem_obras.columns = ['director', 'obras_dirigidas']

  # Aqui vamos pegar o valor de obras do quinto colocado, assim se tiver outro
  # diretor com mesmo número de obras conseguimos incluir no dataset.
  top_diretores = contagem_obras['obras_dirigidas'].nlargest(5).min()
  linhas = contagem_obras['obras_dirigidas'] >= top_diretores
  df_considerando_empate = contagem_obras.loc[ linhas , : ] # definindo o dataset com apenas os diretores do top5


  # Agora vamos organizar o código para printar o top5 diretores com mais filmes na plataforma
  df_agrupado = (df_considerando_empate.groupby('obras_dirigidas')['director']
                                      .apply(list)
                                      .reset_index()
                                      .sort_values(by = 'obras_dirigidas' , ascending = False )
                                      .reset_index(drop=True)
                                      )
  df_agrupado = df_agrupado[['director', 'obras_dirigidas']]



  posicao = 1
  for i in range(len(df_agrupado)):

    num_diretores = len(df_agrupado.loc[ i , 'director'])
    diretor = df_agrupado.loc[i,'director']

    if num_diretores < 2:
      print(f'Em {posicao}º lugar temos o diretor: {diretor}')

    else:
      print(f'Em {posicao}º lugar temos os diretores empatados: {diretor}')

    posicao = (posicao + num_diretores)

  return df_agrupado

def limpar_coluna(df,coluna):

  """Aqui vamos utilizar essa funçã para limpar linhas onde temos valores
     nulos "NaN" de uma coluna especifica"""

  linhas = df[coluna].isna()
  df_aux = df.drop(df.loc[linhas,[coluna]].index)

  return df_aux

def diretores_que_atuaram(df):

  """ Está função além de separar os diretores que atuaram também vai checar os
      nomes únicos pra ver se existem diretores repetidos na lista. E vai checar
      diretores cooperativos para garantir que apenas o diretor que está no cast
      será listado. """

  # limpando as colunas dos valores nulos
  df_diretores = limpar_coluna(df,'director')
  df_diretores = limpar_coluna(df_diretores,'cast')

  df_diretores['diretores_atuaram'] = df_diretores.apply(lambda row: [diretor.strip()
                                                        for diretor in row['director'].split(',')
                                                        if diretor.strip() in str(row['cast'])], axis=1)

  # Filtra apenas os casos onde pelo menos um diretor atuou
  df_filtrado = df_diretores[df_diretores['diretores_atuaram'].apply(len) > 0]
  df_filtrado['diretores_atuaram'].astype(str)

  # Exibe as primeiras linhas onde diretores atuaram
  df_filtrado[['diretores_atuaram' , 'title' , 'cast' , 'director' ]]

  # Obtém todos os diretores que atuaram em seus próprios filmes como uma lista
  todos_diretores = [diretor for lista in df_filtrado['diretores_atuaram'] for diretor in lista]

  # Converte a lista para um conjunto para obter nomes únicos
  diretores_unicos = list(set(todos_diretores))

  # Converte os nomes únicos em um dataframe novamente para melhorar a visualização ao printar 
  df_diretores_que_atuaram = pd.DataFrame(diretores_unicos, columns=['diretores_que_atuaram'])
  
  # Exibe a lista de diretores únicos
  return df_diretores_que_atuaram

def extrair_minutos(tempo):
    if 'min' in tempo:
        return int(tempo.split()[0])  # Pega apenas o número e transforma em int
    return None                       # Retorna None para séries (seasons)

def filmes_minutos(df):

  """ Essa função vai aplicar a função "extrair_minutos" para toda a coluna e
      gerar uma nova coluna com os valores de tempo dos filmes tratados e retorna
      uma função com apenas obras que possamos trabalhar com esses números, descartando
      séries ou qualquer obra de temporadas"""

  df['tempo_minutos'] = df['duration'].apply(lambda x: extrair_minutos(str(x)))

  filmes_df = df.dropna(subset=['tempo_minutos'])

  return filmes_df

def menos_80min_por_periodo( df , periodo ):


  """ Essa função vai realizar um agrupamento da quantidade de filmes por ano, e
      da quantidade de filmes lançados proporcionalmente com menos de 80min.
      Analisando se ao longo dos anos em cada momento onde tivemos filmes mais
      curtos no geral ou se a industria sempre teve o mesmo padrão."""


  # De primeiro ponto vamos retirar qualquer filmes/obra curta metragem para não
  # influienciar no nosso resultado já que nos anos mais recentes do dataframe 
  # se tem uma quantidade muito maior de obras em comparação.
  linhas = df['tempo_minutos'] > 40 
  df_longa_metragem = df.loc[ linhas , : ]

  # realiza um agrupamento contabilizando quantos filmes estão na plataforma por ano de lançamento
  df_filmes_por_ano = df_longa_metragem.loc[ : , ['show_id','release_year'] ].groupby(['release_year']).count().reset_index()

  linhas = df_longa_metragem['tempo_minutos'] <= 80 # Define 80 minutos como corte para verificar ao longo dos anos se
                                                    # realmente acontece alguma mudança ao longo dos anos na proporção
                                                    # de filmes lançados com baixa minutagem.

  filmes_com_menos_de_80min = df_longa_metragem.loc[linhas,:]

  # Mais um agrupamento, dessa vez para separar e contar quantos filmes considerados curtos (com no máximo 80minutos)
  filmes_com_menos_de_80min = filmes_com_menos_de_80min.loc[ : , ['tempo_minutos','release_year'] ].groupby(['release_year']).count().reset_index()

  # aqui vamos juntar os dois dataframes anteriores, para entender a proporção que os filmes curtos tem no total de
  # filmes lançados no ano. Mais uma vez para garantir um resultado justo já que temos uma quantidade muito maior
  # de filmes adicionados que foram lançados nos anos mais recentes do dataframe
  filmes_lancados_com_menos_80min = pd.merge( filmes_com_menos_de_80min , df_filmes_por_ano , on='release_year' )

  # realizamos um calculo para proporção desses filmes curtos e criamos uma coluna para representar eles.
  filmes_lancados_com_menos_80min['porcentagem_filmes_curtos'] = filmes_lancados_com_menos_80min['tempo_minutos']/filmes_lancados_com_menos_80min['show_id']

  # Aqui para melhor visualização e entendimento dos resultados, vamos agrupar por periodos, por exemplo a cada
  # decada, a cada 5 anos...
  filmes_lancados_com_menos_80min['anos'] = (filmes_lancados_com_menos_80min['release_year'] // periodo) * periodo


  menos_de_80min_por_periodo = filmes_lancados_com_menos_80min.loc[ : , ['anos', 'porcentagem_filmes_curtos'] ].groupby(['anos']).mean().reset_index()
  
  # Para essa análise achei importante definir uma data inicial onde conseguiriamos avaliar melhor os resultados, evitando
  # anos praticamente nulos de filmes, por isso considerei iniciar a partir dos anos 2000.
  linhas = menos_de_80min_por_periodo['anos'] >= 2000
  menos_de_80min_por_periodo = menos_de_80min_por_periodo.loc[ linhas , : ].reset_index()

  # para melhor vizualização vamos adicionar o intervalo na plotagem e não apenas um ano. Vai ficar "2000-2005"...
  menos_de_80min_por_periodo['intervalo'] = menos_de_80min_por_periodo['anos'].astype(str) + '-' + (menos_de_80min_por_periodo['anos'] + 5).astype(str)
  menos_de_80min_por_periodo.iloc[-1,3] = '2020-2021'
  menos_de_80min_por_periodo['porcentagem_filmes_curtos'] = round((menos_de_80min_por_periodo['porcentagem_filmes_curtos']*100), 2)
  menos_de_80min_por_periodo = menos_de_80min_por_periodo[['intervalo','porcentagem_filmes_curtos']]

  return menos_de_80min_por_periodo

#------------------------------------------------------------------------------------------------------
#                                    MAIN CODE
#------------------------------------------------------------------------------------------------------

# Lendo o arquivo

df_netflix = ler_arquivo(f'data/netflix_titles.csv')

# Antes de prosseguir para as perguntas foi checado coluna por coluna para entender o seu tipo e sua formataçãp e valores -
# - únicos para realização do data cleaning. A escolha tomada é seguir para as perguntas e realizar limpezas por colunas apenas -
# - no seu momento de uso, para garantir a integridade geral das informações e evitar mudanças em seus resultados reais.

st.header("Dashboard - Desafio VExpenses")
df_netflix['date_added'] = df_netflix['date_added'].str.strip()
df_netflix['data_adicionado'] = pd.to_datetime(df_netflix['date_added'], format='%B %d, %Y')
df_netflix['ano_adicionado'] = df_netflix['data_adicionado'].dt.year  

with st.container():

    st.title('Métricas Gerais')
    col1, col2, col3 = st.columns(3)

    with col1:
       qnt_filmes = filmes_cadastrados(df_netflix)
    #    col1.metric(label='Filmes Cadastrados',value=qnt_filmes)
       st.markdown("##### Filmes Cadastrados")
       
       st.markdown(f"### - {qnt_filmes}")

 
    with col2:

        ultimo_filme_data = df_netflix['data_adicionado'].max()
        ultimo_filme = df_netflix[df_netflix['data_adicionado'] == ultimo_filme_data]['title'].iloc[0]
        # col2.metric(label='Úçtimo filmes adicionado',value=ultimo_filme)
        st.markdown("##### Último filme adicionado na plataforma:")
        
        st.markdown(f"##### - {ultimo_filme}")
    
    with col3:

        primeiro_filme_data = df_netflix['data_adicionado'].min()

        primeiro_filme = df_netflix[df_netflix['data_adicionado'] == primeiro_filme_data]['title'].iloc[0]
        # col3.metric(label='Primeiro filme adicionado',value=primeiro_filme)
        st.markdown("##### Primeiro filme adicionado na plataforma:")
        
        st.markdown(f"##### - {primeiro_filme}")

with st.container():
   st.markdown('<hr style="border:1px solid #73B3A6;">', unsafe_allow_html=True)
   col1, col2 = st.columns(2)
   
   with col1:
    st.markdown('##### Quantidade de obras por data de lançamento')
    filmes_por_lancamento = df_netflix.loc[ : , ['release_year','show_id'] ].groupby(['release_year']).count().reset_index()
    fig = px.bar( filmes_por_lancamento , x= 'release_year' , y= 'show_id', color_discrete_sequence=['#3B738F'] )
    st.plotly_chart(fig,use_container_width=True)

   with col2:
    st.markdown('##### Quantidade de obras por data que foi adicionado')

    filmes_adicionados_por_ano = df_netflix.loc[ : , ['ano_adicionado','show_id'] ].groupby(['ano_adicionado']).count().reset_index()

    fig = px.bar( filmes_adicionados_por_ano , x= 'ano_adicionado' , y= 'show_id' , color_discrete_sequence=['#3B738F'])
    st.plotly_chart(fig,use_container_width=True)


with st.container():
  st.markdown('<hr style="border:1px solid #73B3A6;">', unsafe_allow_html=True)

  col1, col2 = st.columns(2)

  with col1:
    st.markdown('##### Quantidade de obras por tipo:')
    quantidade_de_obras_por_tipo = df_netflix.loc[ : , ['type','show_id']].groupby(['type']).count().reset_index()

    fig = px.pie( quantidade_de_obras_por_tipo , names='type' , values= 'show_id' , hole=0.4, color_discrete_sequence=px.colors.sequential.Teal_r)
    fig.update_traces(textinfo='label+percent', showlegend=False)
    st.plotly_chart(fig,use_container_width=True)

  with col2:
    st.markdown('##### Quantidade de obras por classificação:')

    quantidade_de_obras_por_rating = df_netflix.loc[ : , ['rating','show_id']].groupby(['rating']).count().reset_index()

    fig = px.pie( quantidade_de_obras_por_rating , names='rating' , values= 'show_id' , hole=0.4 , color_discrete_sequence=px.colors.sequential.Teal_r)
    fig.update_traces(textinfo='label+percent', showlegend=False)
    st.plotly_chart(fig,use_container_width=True)


with st.container():
  st.markdown('<hr style="border:1px solid #73B3A6;">', unsafe_allow_html=True)
  
  st.markdown("##### Filmes onde os diretores dirigiram e atuaram")

  diretores_que_atuaram(df_netflix)
    
  
#   col1, col2 = st.columns(2)

#   with col1:
#     st.markdown("##### coluna1")

#     top_5 = top_5_diretores(df_netflix)
#     st.dataframe(top_5)





