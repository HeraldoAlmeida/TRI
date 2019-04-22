#==============================================================================
#  TRI - ENEM
#
#    Sera usado o modelo 3PL com parametro c fixo em 0.2 para todos os itens
#
#    A probabilidade P de uma resposta correta do participante j ao item i
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

ENEM2017_ITENS         = '../../../_Datasets/microdados_enem2017/ITENS_PROVA_2017.csv'
ENEM2017_PARTICIPANTES = '../../../_Datasets/microdados_enem2017/MICRODADOS_ENEM_2017.csv'

#==============================================================================
#  CONFIGURACOES
#==============================================================================

FILTRAR_SOMENTE_PROVAS_PRINCIPAIS = True

TRI_NOTA_MEDIA                                 = 500.0
TRI_NOTA_DESVIO_PADRAO                         = 100.0

REGRESSAO_LOGISTICA_AJUSTE_THETA_PENALIDADE    = 'l2'
REGRESSAO_LOGISTICA_AJUSTE_THETA_REGULARIZACAO = 1.0
REGRESSAO_LOGISTICA_AJUSTE_AB_PENALIDADE       = 'l2'
REGRESSAO_LOGISTICA_AJUSTE_AB_REGULARIZACAO    = 1.0

NUM_MAX_ITERACOES                              = 5

#==============================================================================
#  MODULOS PYTHON IMPORTADOS
#==============================================================================

import pandas as pd
import numpy  as np
import math

from sklearn.metrics      import mean_squared_error, r2_score
from sklearn.linear_model import LogisticRegression

#------------------------------------------------------------------------------
#  Importar os itens das provas (conjunto de treinamento)
#------------------------------------------------------------------------------

df_itens_prova = pd.read_csv(
        ENEM2017_ITENS,
        encoding = "ISO-8859-1",
        sep = ';',
        usecols=[
                'CO_PROVA',
                'CO_POSICAO',
                'CO_ITEM',
                'SG_AREA',
                'TP_LINGUA'
                ]
        )
    
#==============================================================================
#  PARA CADA AREA DE CONHECIMENTO ...
#==============================================================================

for area in [ 'LC' , 'CH' , 'CN' , 'MT' ] :

    print ( '\nArea de Conhecimento %s :\n' % area )
   
    #--------------------------------------------------------------------------
    #  Importar dados do desempenho dos participantes na area selecionada
    #--------------------------------------------------------------------------
    
    df_participantes = pd.read_csv( 
            ENEM2017_PARTICIPANTES, 
            encoding = "ISO-8859-1",
            sep = ';', 
            usecols=[
                    'NU_INSCRICAO',
                    'TP_LINGUA',
                    'TP_PRESENCA_'+area,
                    'CO_PROVA_'+area,
                    'NU_NOTA_'+area,
                    'TX_RESPOSTAS_'+area,
                    'TX_GABARITO_'+area
                    ]
            ,nrows=100000
            ).dropna().sort_values(by=['NU_INSCRICAO'])


    df_participantes.rename(columns={
            'TP_PRESENCA_'+area:'TP_PRESENCA',
            'CO_PROVA_'+area:'CO_PROVA',
            'NU_NOTA_'+area:'NU_NOTA',
            'TX_RESPOSTAS_'+area:'TX_RESPOSTAS',
            'TX_GABARITO_'+area:'TX_GABARITO'
            }, 
                 inplace=True)
 

#    df_participantes.columns=[
#                    'NU_INSCRICAO',
#                    'TP_LINGUA',
#                    'TP_PRESENCA',
#                    'CO_PROVA',
#                    'NU_NOTA',
#                    'TX_RESPOSTAS',
#                    'TX_GABARITO'
#                    ]
    
    #--------------------------------------------------------------------------
    #  Filtrar participantes:
    #   - descartar participantes ausentes ou eliminados na area selecionada
    #   - descartar participantes com notas zeradas na area selecionada
    #--------------------------------------------------------------------------
    
    df_participantes = df_participantes.loc[df_participantes['TP_PRESENCA'] == 1]
    df_participantes = df_participantes.loc[df_participantes['NU_NOTA'    ] >  0]

    #--------------------------------------------------------------------------
    #  Filtrar itens:
    #    - considerar somente os itens da area de conhecimento a ser medida
    #--------------------------------------------------------------------------
    
    df_itens  = df_itens_prova.loc[df_itens_prova['SG_AREA'] == area].sort_values(by=['CO_ITEM']).drop(columns=['SG_AREA'])
    
    #--------------------------------------------------------------------------
    #  Filtro opcional para considerar somente as provas principais
    #--------------------------------------------------------------------------

    if FILTRAR_SOMENTE_PROVAS_PRINCIPAIS:
        df_itens         = df_itens.loc[df_itens['CO_PROVA'] <= 406]
        df_participantes = df_participantes.loc[df_participantes['CO_PROVA'] <= 406]

    #--------------------------------------------------------------------------
    #
    #  Iniciar lista de itens
    #
    #    item               --> codigo identificador do item
    #    item_parametro_a   --> parametro a do modelo TRI do item
    #    item_parametro_b   --> parametro b do modelo TRI do item
    #    item_participantes --> lista de participantes que responderam ao item
    #    item_resultados    --> lista de resultados (1=acerto; 0=erro) de cada participante no item
    #
    #--------------------------------------------------------------------------

    item             = df_itens['CO_ITEM'].unique()
    item_parametro_a = np.empty ( ( item.size , 1 ) , dtype=np.float64 );
    item_parametro_b = np.empty ( ( item.size , 1 ) , dtype=np.float64 );

    #--------------------------------------------------------------------------
    #
    #  Iniciar lista de participantes
    #
    #    participante            --> codigo identificador do participante
    #    participante_prova      --> codigo da prova que o participante respondeu
    #    participante_lingua     --> lingua estrangeira escolhida pelo participante
    #    participante_nota       --> nota real do participante no exame
    #    participante_theta      --> nota estimada para o participante
    #    participante_resultados --> array com a correcao das 45 questoes ( 1 = acerto; 0 = erro )
    #
    #--------------------------------------------------------------------------

    participante         = df_participantes['NU_INSCRICAO'].values
    participante_nota    = df_participantes['NU_NOTA'].values
    
    participante_acertos = np.empty ( ( participante.size )      , dtype=np.uint8   )
    participante_theta   = np.empty ( ( participante.size ,  1 ) , dtype=np.float32 )
    
    #--------------------------------------------------------------------------
    #  Preencher a matriz de resultados
    #--------------------------------------------------------------------------

    resultado = np.ones ( ( participante.size , item.size ) , dtype=np.uint8 ) * 2
    
    j = 0
    
    for p in df_participantes.itertuples():
        
        itens = np.searchsorted ( item , df_itens.loc[df_itens['CO_PROVA'] == p.CO_PROVA]['CO_ITEM'].values )

        resultados = np.asarray([ int(x==y) for (x,y) in zip(list(p.TX_RESPOSTAS), list(p.TX_GABARITO))])
        
        if area == 'LC':
            if p.TP_LINGUA == 0:
                itens      = np.concatenate ( ( itens[0:5]      , itens[10:]      ) )
                resultados = np.concatenate ( ( resultados[0:5] , resultados[10:] ) )
            else:
                itens      = itens[5:]
                resultados = resultados[5:]

        resultado[j,itens] = resultados
        
        acertos = sum(resultados[resultados==1])
        participante_acertos[j] = acertos
        j = j + 1
    
    #--------------------------------------------------------------------------
    #  Inicializar o parametro theta para todos os participantes
    #--------------------------------------------------------------------------

    participante_theta = ( participante_acertos - np.mean(participante_acertos) ) / np.std(participante_acertos)
    
    #--------------------------------------------------------------------------
    #  INICIALIZACAO DOS MODELOS DE REGRESSSAO LOGISTICA
    #--------------------------------------------------------------------------

    # modelo para ajuste dos parametros dos itens (a e b)     
    
    lr_ab = LogisticRegression(
            penalty        = REGRESSAO_LOGISTICA_AJUSTE_AB_PENALIDADE, 
            C              = REGRESSAO_LOGISTICA_AJUSTE_AB_REGULARIZACAO,
            fit_intercept  = True
            )
        
    # modelo para ajuste da habilidade dos participantes (theta)
    
    lr_theta = LogisticRegression(
            penalty        = REGRESSAO_LOGISTICA_AJUSTE_AB_PENALIDADE, 
            C              = REGRESSAO_LOGISTICA_AJUSTE_AB_REGULARIZACAO,
            fit_intercept  = False
            )
    
    #--------------------------------------------------------------------------
    #  INICIO DO PROCESSO ITERATIVO DE ESTIMACAO DA NOTA (parametro theta)
    #--------------------------------------------------------------------------

    #----------------------------------------------------------------------
    #
    #  Otimizar a(i), b(i) e c(i) para os valores atuais de t(j):
    #
    #                         1 - c(i)
    #    c(i) + --------------------------------------- = p(j,i)
    #            1 + exp ( -a(i) * (t(j) - b(i)) )
    #
    #  Considerando c constante igual a 0.2 :
    #
    #                           0.8
    #    0.2 + --------------------------------------- = p(j,i)
    #           1 + exp ( -a(i) * (theta(j) - b(i)) )
    #
    #                      1                        p(j,i) - 0.2
    #    --------------------------------------- = --------------
    #     1 + exp ( -a(i)*theta(j) + a(i)*b(i)) )         0.8
    #
    #----------------------------------------------------------------------
             
    
    for iter in range(NUM_MAX_ITERACOES) :

        #----------------------------------------------------------------------
        #  Calcular RMSE entre a nota estimada e a nota real
        #----------------------------------------------------------------------
     
        participante_nota_estimada = participante_theta * np.std(participante_nota) + np.mean(participante_nota)
    
        print ( '\nITERACAO %d :' % iter                                                       )
        print ( 'RMSE = %.3f'     % math.sqrt(mean_squared_error ( participante_nota , participante_nota_estimada )))
        print ( 'R2   = %.3f\n'   %                     r2_score ( participante_nota , participante_nota_estimada ) )

        #----------------------------------------------------------------------
        #  Estimar os parametros a e b para cada item
        #----------------------------------------------------------------------

        for i in range(item.size) :
           
            indices_dos_participantes = np.array((resultado[:,i]-2).nonzero()[0])

            lr_ab.fit(
                    participante_theta [ indices_dos_participantes     ].reshape(-1,1) ,
                    resultado          [ indices_dos_participantes , i ]
                    )
            
            item_parametro_a[i] =   lr_ab.coef_
            item_parametro_b[i] =  -lr_ab.intercept_ / lr_ab.coef_
    
#        print ( 'item_parametro_a[i] = %f'   % item_parametro_a[i] )
#        print ( 'item_parametro_b[i] = %f\n' % item_parametro_b[i] )
        
#        for xi in range(-6,7,1):
#            x = xi/2
#            print ( 'x = %f'%x , 'y = %f'% (1/(1+math.exp(-item_parametro_a[i]*(x-item_parametro_b[i])))) )
            
        #----------------------------------------------------------------------
        #  Estimar o parametro theta para cada participante
        #----------------------------------------------------------------------
        
        for j in range(participante.size) :

            indices_dos_itens = np.array((resultado[j,:]-2).nonzero()[0])

            if np.sum(resultado[j,indices_dos_itens]) == 0 :
                participante_theta[j] = 0.0
                continue

            lr_theta.fit(
                    item_parametro_a [     indices_dos_itens ].reshape(-1,1) ,
                    resultado        [ j , indices_dos_itens ]
                    )

            participante_theta[j] = lr_theta.coef_ + item_parametro_b[i]

        #----------------------------------------------------------------------
        #  Normalizar theta
        #----------------------------------------------------------------------
        
        participante_theta = ( participante_theta - np.mean(participante_theta) ) / np.std(participante_theta)

        
#        print ( '\nparticipante_theta[j] = %f\n' % participante_theta[j] )
        
            
