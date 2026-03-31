"""
Exemplo de notebook para EDA (Exploratory Data Analysis)

Este arquivo contém o template com as principais seções de análise exploratória.
Customize conforme seus dados específicos.
"""

# # Tech Challenge - Exploratória Data Analysis (EDA)
# 
# **Objetivo**: Entender a estrutura, distribuição e características dos dados antes do modelo.

# ## 1. Setup & Imports

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

# Configurações de visualização
sns.set_theme(style="darkgrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

print("Imports realizados com sucesso!")

# ## 2. Carregamento de Dados

# Substitua pelos seus dados
# df = pd.read_csv('data/raw/dataset.csv')

# Para fins de demonstração, vamos criar um dataset fictício
np.random.seed(42)
n_samples = 1000

df = pd.DataFrame({
    'feature_1': np.random.normal(loc=50, scale=15, size=n_samples),
    'feature_2': np.random.normal(loc=100, scale=25, size=n_samples),
    'feature_3': np.random.uniform(0, 1, size=n_samples),
    'target': np.random.binomial(1, 0.3, size=n_samples),  # Classificação binária
})

print(f"Dataset carregado com sucesso!")
print(f"Shape: {df.shape}")

# ## 3. Visão Geral dos Dados

# ### 3.1 Primeiras Linhas
print("\n📊 Primeiras 5 linhas:")
print(df.head())

# ### 3.2 Info dos Dados
print("\n📋 Informações do Dataset:")
print(df.info())

# ### 3.3 Estatísticas Descritivas
print("\n📈 Estatísticas Descritivas:")
print(df.describe())

# ## 4. Verificação de Valores Faltantes

print("\n🔍 Valores Faltantes:")
missing = df.isnull().sum()
missing_pct = 100 * missing / len(df)
missing_df = pd.DataFrame({
    'Missing_Count': missing,
    'Percentage': missing_pct
})
print(missing_df[missing_df['Missing_Count'] > 0])

# ## 5. Análise de Distribuições

# ### 5.1 Univariada - Histogramas
# fig, axes = plt.subplots(1, 3, figsize=(15, 4))
# 
# for idx, col in enumerate(df.columns[:-1]):
#     axes[idx].hist(df[col], bins=30, edgecolor='black', alpha=0.7)
#     axes[idx].set_title(f'Distribuição de {col}')
#     axes[idx].set_xlabel(col)
#     axes[idx].set_ylabel('Frequência')
# 
# plt.tight_layout()
# plt.show()

# ### 5.2 Box Plot - Detecção de Outliers
# fig, axes = plt.subplots(1, 3, figsize=(15, 4))
# 
# for idx, col in enumerate(df.columns[:-1]):
#     axes[idx].boxplot(df[col])
#     axes[idx].set_title(f'Box Plot - {col}')
#     axes[idx].set_ylabel(col)
# 
# plt.tight_layout()
# plt.show()

# ## 6. Análise Bivariada - Correlações

print("\n🔗 Matriz de Correlação:")
corr_matrix = df.corr()
print(corr_matrix)

# Visualizar correlações
# plt.figure(figsize=(8, 6))
# sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
# plt.title('Matriz de Correlação')
# plt.show()

# ## 7. Análise da Variável Alvo

print("\n🎯 Análise da Variável Alvo:")
print(df['target'].value_counts())
print(f"\nDistribuição (%):")
print(df['target'].value_counts(normalize=True) * 100)

# # Gráfico da distribuição do target
# fig, axes = plt.subplots(1, 2, figsize=(12, 4))
# 
# df['target'].value_counts().plot(kind='bar', ax=axes[0], color=['blue', 'orange'])
# axes[0].set_title('Distribuição da Classe')
# axes[0].set_ylabel('Contagem')
# axes[0].set_xticklabels(['Classe 0', 'Classe 1'], rotation=0)
# 
# df['target'].value_counts(normalize=True).plot(kind='pie', ax=axes[1], autopct='%1.1f%%')
# axes[1].set_title('Proporção de Classes')
# 
# plt.tight_layout()
# plt.show()

# ## 8. Estatísticas por Grupo (Target)

print("\n👥 Estatísticas por Classe:")
print(df.groupby('target').describe())

# ## 9. Detecção de Outliers

def detect_outliers_iqr(data, col):
    Q1 = data[col].quantile(0.25)
    Q3 = data[col].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return data[(data[col] < lower_bound) | (data[col] > upper_bound)]

print("\n⚠️ Outliers detectados (IQR method):")
for col in df.columns[:-1]:
    outliers = detect_outliers_iqr(df, col)
    print(f"{col}: {len(outliers)} outliers ({len(outliers)/len(df)*100:.2f}%)")

# ## 10. Skewness & Kurtosis

print("\n📐 Skewness (Assimetria):")
for col in df.columns[:-1]:
    skew = df[col].skew()
    print(f"{col}: {skew:.4f}")

print("\n📐 Kurtosis (Curtose):")
for col in df.columns[:-1]:
    kurt = df[col].kurtosis()
    print(f"{col}: {kurt:.4f}")

# ## 11. Multicolinearidade

print("\n🔗 Verificação de Multicolinearidade (VIF):")
from statsmodels.stats.outliers_influence import variance_inflation_factor

X = df.drop('target', axis=1)
vif_data = pd.DataFrame()
vif_data["Feature"] = X.columns
vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
print(vif_data)

# ## 12. Insights & Conclusões

# ### Resumo dos Achados
insights = """
## 🎯 Principais Insights:

1. **Distribuição dos Dados**:
   - Feature_1: Distribuição normal com média ~50
   - Feature_2: Distribuição normal com média ~100
   - Feature_3: Distribuição uniforme entre 0-1

2. **Valores Faltantes**:
   - Não há valores faltantes no dataset

3. **Outliers**:
   - Poucos outliers detectados
   - Recomenta-se manter ou aplicar técnicas robustas

4. **Desbalanceamento de Classes**:
   - Classe 0: ~70%
   - Classe 1: ~30%
   - Recomenda-se usar weighted loss ou técnicas de balanceamento

5. **Correlações**:
   - Baixa correlação entre features
   - Boa sinal para evitar multicolinearidade

## ✅ Recomendações para Modelagem:

- ✓ Usar weighted cross-entropy loss
- ✓ Aplicar normalização StandardScaler
- ✓ Considerar data augmentation para classe minoritária
- ✓ Usar stratified k-fold para validação
- ✓ Monitorar métrica F1-score (não apenas acurácia)
"""

print(insights)

# ## 13. Preparação para Treinamento

print("\n🔄 Próximos Passos:")
print("1. Feature Engineering")
print("2. Normalização/Padronização")
print("3. Divisão Treino/Validação/Teste")
print("4. Treinamento do Modelo")
print("5. Avaliação & Ajustes")
