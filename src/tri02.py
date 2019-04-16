#==============================================================================
#  TRI - ENEM
#
#    Sera usado o modelo 3PL com parametero c fixo em 0.2 para todos os itens
#
#    a probabilidade P de uma resposta correta do participante j ao item i
#    (uji = 1), em função do parâmetro de proficiência hj e dos parâmetros
#    do item ai, bi e ci, é dada por
#
#                                                  1 - c(i)
#      P ( u(j,i)=1 | h(j) )  =  c(i) + -----------------------------------
#                                        1 + exp ( -a(i) * (h(j) - b(i)) )
#
#==============================================================================

#==============================================================================
#  LOCALIZACAO DOS ARQUIVOS DE ENTRADA E SAIDA DE DADOS
#==============================================================================

ITENS_TREINAMENTO = '../../../_Datasets/microdados_enem2017/ITENS_PROVA_2017.csv'
DADOS_TREINAMENTO = '../../../_Datasets/microdados_enem2017/MICRODADOS_ENEM_2017.csv'

#==============================================================================
#  PARAMETROS DE CONFIGURACAO
#==============================================================================


#==============================================================================
#  MODULOS PYTHON IMPORTADOS
#==============================================================================

import pandas as pd
import numpy  as np
#import math

#from sklearn.metrics import mean_squared_error, r2_score

#------------------------------------------------------------------------------
#  Importar os itens das provas (conjunto de treinamento)
#------------------------------------------------------------------------------

df_itens = pd.read_csv(
        ITENS_TREINAMENTO,
        encoding = "ISO-8859-1",
        sep = ';',
        usecols=['CO_PROVA','CO_POSICAO','CO_ITEM','SG_AREA','TP_LINGUA']
        )
    
#==============================================================================
#  PARA CADA AREA DE CONHECIMENTO ...
#==============================================================================

for area in [ 'MT' , 'CH' , 'CN' , 'LC' ] :

    print ( '\nArea de Conhecimento %s :\n' % area )
   
    #--------------------------------------------------------------------------
    #  Considerar somente os itens da area de conhecimento a ser medida
    #--------------------------------------------------------------------------
    
    df_itens_area = df_itens.loc[df_itens['SG_AREA'] == area]
    df_itens_area = df_itens_area.drop(columns=['SG_AREA'])
    
    #--------------------------------------------------------------------------
    #  Importar dados do desempenho dos participantes na area selecionada
    #--------------------------------------------------------------------------
    
    dados = pd.read_csv( 
            DADOS_TREINAMENTO, 
            encoding = "ISO-8859-1",
            sep = ';', 
            usecols=[
                    'NU_INSCRICAO',
                    'TP_LINGUA',
                    'TP_PRESENCA_'+area,
                    'CO_PROVA_'+area,
                    'NU_NOTA_'+area,
                    'TX_RESPOSTAS_'+area,
                    'TX_GABARITO_'+area]
            ,nrows=100000
            ).dropna()
    
    #--------------------------------------------------------------------------
    #  Eliminar participantes com notas zeradas (prova em branco)
    #--------------------------------------------------------------------------
    
    dados = dados.loc[dados['NU_NOTA_'+area] > 0]

    #--------------------------------------------------------------------------
    #  Montar lista de participantes
    #--------------------------------------------------------------------------

    participante_id      = df_dados['NU_INSCRICAO'].values
    participante_theta   = np.zeros((participante_id.size))
    participante_itens   = np.zeros((participante_id.size,45))
    participante_acertos = np.zeros((participante_id.size,45))
    
    for p in range(participante_id.size):
        prova = dados['CO_PROVA_'+area].iloc[p] * 10
        if area == 'LC' and dados['TP_LINGUA'].iloc[p] == 1 :
            
            tp_lingua = dados['TP_LINGUA_'+area].iloc[p]

        for j in range(n_participantes) :
            
            resposta = microdados['TX_RESPOSTAS_'+area].iloc[j]
            gabarito = microdados['TX_GABARITO_' +area].iloc[j]


    #--------------------------------------------------------------------------
    #  Montar lista de itens
    #--------------------------------------------------------------------------

    item_id            = df_itens_area['CO_ITEM'].drop_duplicates().values    
    item_parametros    = np.zeros((item_id.size,2))
    item_participantes = np.zeros((item_id.size))
    item_acertos       = np.zeros((item_id.size))

    #--------------------------------------------------------------------------
    #  Montar lista de provas
    #--------------------------------------------------------------------------

    prova_id = df_itens_area['CO_PROVA'].drop_duplicates().values * 10

    if area == 'LC' :
        prova_id = np.concatenate((prova_id,prova_id+1))   

    prova_itens = np.zeros((prova_id.size,45))

    if     

    #------------------------------------------------------------------------------
    #  Montar a matriz de acertos
    #------------------------------------------------------------------------------
    
    acerto = np.zeros((participante_id.size,45))

    for p in provas :
        
        microdados_prova = microdados.loc[(microdados['CO_PROVA_'+area] == p)]
        
        for j in range(n_participantes) :
            
            resposta = microdados['TX_RESPOSTAS_'+area].iloc[j]
            gabarito = microdados['TX_GABARITO_' +area].iloc[j]
            
            i = 0
            
            for k in range(len(gabarito)):
                
                if resposta[k] == '9' :
                    continue
            
                if resposta[k] == gabarito[k] :
                    acerto[j][i] = 1
                else :
                    acerto[j][i] = 0
                    
                i = i + 1

   
