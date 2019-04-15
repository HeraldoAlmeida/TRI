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

ITENSPROVA_2017_URL = '../../../_Datasets/microdados_enem2017/ITENS_PROVA_2017.csv'
MICRODADOS_2017_URL = '../../../_Datasets/microdados_enem2017/MICRODADOS_ENEM_2017.csv'

#==============================================================================
#  PARAMETROS DE CONFIGURACAO
#==============================================================================


#==============================================================================
#  MODULOS PYTHON IMPORTADOS
#==============================================================================

import pandas as pd
import numpy  as np
import math

from sklearn.metrics import mean_squared_error, r2_score


#==============================================================================
#  PARA CADA AREA DE CONHECIMENTO ...
#==============================================================================

for area in [ 'MT' , 'CH' , 'CN' , 'LC' ] :

    print ( '\nArea de Conhecimento %s :\n' % area )
   
    #print('MSE  = %.3f' %           mean_squared_error(y_train, y_pred_train) )
    #print('RMSE = %.3f' % math.sqrt(mean_squared_error(y_train, y_pred_train)))
    #print('R2   = %.3f' %                     r2_score(y_train, y_pred_train) )

    #------------------------------------------------------------------------------
    #  Importar dados dos itens das provas
    #------------------------------------------------------------------------------
    
    itens = pd.read_csv(
            ITENSPROVA_2017_URL,
            encoding = "ISO-8859-1",
            sep = ';',
            #usecols=['CO_PROVA','CO_POSICAO','CO_ITEM','SG_AREA','TP_LINGUA']
            usecols=['CO_PROVA','CO_POSICAO','CO_ITEM','SG_AREA']
            )
    
    itens = itens.loc[itens['CO_PROVA'] <= 406] # selecionar somente itens das provas "padrao"
    itens = itens.loc[itens['SG_AREA'] == area] # selecionar somente itens das provas da area
    itens = itens.drop(columns=['SG_AREA'])     # descartar o campo SG_AREA
    
    itens.set_index(['CO_PROVA','CO_POSICAO'])
    
#    itens_distintos = itens['CO_ITEM'].drop_duplicates()
#    
#    for i in itens_distintos :
#        
#        itens.loc[(itens['CO_ITEM'] == itens_distintos) & (df['column_name'] <= B)]

    
    #------------------------------------------------------------------------------
    #  Importar microdados
    #------------------------------------------------------------------------------
    
    microdados = pd.read_csv( 
            MICRODADOS_2017_URL, 
            encoding = "ISO-8859-1",
            sep = ';', 
            usecols=[
                    'NU_INSCRICAO',
                    'TP_PRESENCA_'+area,
                    'CO_PROVA_'+area,
                    'NU_NOTA_'+area,
                    'TX_RESPOSTAS_'+area,
                    'TX_GABARITO_'+area]
            ,nrows=100000
            ).dropna()
    
    microdados = microdados.loc[microdados['CO_PROVA_'+area] <= 406]   # selecionar somente respostas aos itens das provas "padrao"

    microdados = microdados.loc[microdados['NU_NOTA_'+area] > 0]       # eliminar participantes com notas zeradas (prova em branco)

    #------------------------------------------------------------------------------
    #  Calcular informacoes estatisticas de proficiencia
    #------------------------------------------------------------------------------
    
    nota_real = microdados['NU_NOTA_'+area].values
    
    n_participantes  = np.size(nota_real)
    media_nota_real  = np.mean(nota_real)
    desvio_nota_real = np.std(nota_real)
    
    print ( '  Numero de Participantes      = %d\n'     % n_participantes  )
    print ( '  Media  da Nota Real          =   %.4f  ' % media_nota_real  )
    print ( '  Desvio da Nota Real          =   %.4f\n' % desvio_nota_real )

    #------------------------------------------------------------------------------
    #  Montar a matriz de acertos
    #------------------------------------------------------------------------------
    
    #acerto = [[0 for col in range(45)] for row in range(n_participantes)]
    acerto = np.zeros( (n_participantes, 45) )

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

    qtd_acertos    = np.sum(acerto,axis=1)
    media_acertos  = np.mean(qtd_acertos)
    desvio_acertos = np.std(qtd_acertos) 

    print ( '  Media  do Numero de Acertos  =   %.4f  ' % media_acertos    )
    print ( '  Desvio da Numero de Acertos  =   %.4f\n' % desvio_acertos   )
        
    #------------------------------------------------------------------------------
    #  Normalizar o numero de acertos (valor inicial do parametro theta)
    #------------------------------------------------------------------------------
    
    theta = ( qtd_acertos - media_acertos ) / desvio_acertos

    #------------------------------------------------------------------------------
    #  INICIO DO PROCESSO ITERATIVO DE ESTIMACAO DA NOTA (parametro theta)
    #------------------------------------------------------------------------------
    
    for iter in range(30) :

        #------------------------------------------------------------------------------
        #  Calcular RMSE entre a nota estimada e a nota real
        #------------------------------------------------------------------------------
     
        nota_estimada = theta * 100 + 500
    
        print ( '\nITERACAO %d :' % iter                                                       )
        print ( 'RMSE = %.3f'     % math.sqrt(mean_squared_error ( nota_real , nota_estimada )))
        print ( 'R2   = %.3f\n'   %                     r2_score ( nota_real , nota_estimada ) )

        #------------------------------------------------------------------------------
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
        #------------------------------------------------------------------------------
             
        from sklearn.linear_model import LogisticRegression
    
        lr = LogisticRegression(penalty='l2', C=1)
        
        a = np.zeros((45))
        b = np.zeros((45))
        
        for i in range(45) :
            lr.fit ( theta.reshape(-1,1) , acerto[:,i] )
            a[i] = lr.coef_
            b[i] = -lr.intercept_ / a[i]
            
        lr = LogisticRegression(penalty='l2', C=1, fit_intercept=False)

        ALPHA = 0.125    
        for j in range(n_participantes) :
            if np.sum(acerto[j,:]) == 0 :
                print (' j = %d\n' % j )
                continue
            lr.fit ( a.reshape(-1,1) , acerto[j,:] )
            thetaj   = lr.coef_ + b[i]
            theta[j] = theta[j] + ALPHA * (thetaj-theta[j])
        

