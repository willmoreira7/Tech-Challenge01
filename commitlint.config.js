// Configuração do commitlint com Conventional Commits
// Referência: https://commitlint.js.org | https://www.conventionalcommits.org
//
// Mapeamento de tipos para versão semântica (usado pelo semantic-release):
//   fix, perf, revert  → PATCH  (0.0.x)
//   feat               → MINOR  (0.x.0)
//   feat! ou BREAKING CHANGE → MAJOR  (x.0.0)
//
// Tipos que NÃO incrementam versão: docs, style, refactor, test, chore, ci, build

module.exports = {
  extends: ['@commitlint/config-conventional'],

  rules: {
    // Tipos permitidos
    'type-enum': [
      2, // nível error (bloqueia o commit)
      'always',
      [
        'feat',     // Nova funcionalidade → incrementa MINOR
        'fix',      // Correção de bug     → incrementa PATCH
        'docs',     // Apenas documentação (sem incremento de versão)
        'style',    // Formatação, ponto-e-vírgula, etc. (sem lógica)
        'refactor', // Refatoração sem fix nem feat
        'test',     // Adição ou correção de testes
        'chore',    // Manutenção: build, deps, config
        'perf',     // Melhoria de performance → incrementa PATCH
        'ci',       // Mudanças em arquivos/scripts de CI
        'build',    // Mudanças no sistema de build ou dependências externas
        'revert',   // Reverter commit anterior → incrementa PATCH
      ],
    ],

    // O escopo é opcional mas, quando informado, deve estar em lowercase
    'scope-case': [2, 'always', 'lower-case'],

    // A descrição é obrigatória
    'subject-empty': [2, 'never'],

    // Sem ponto final na descrição: "fix: login page" não "fix: login page."
    'subject-full-stop': [2, 'never', '.'],

    // Descrição em lowercase (evita "Fix: Login Page")
    'subject-case': [2, 'never', ['start-case', 'pascal-case', 'upper-case']],

    // Linha de cabeçalho com no máximo 100 caracteres
    'header-max-length': [2, 'always', 100],

    // Corpo do commit com no máximo 200 caracteres por linha (warning apenas)
    'body-max-line-length': [1, 'always', 200],
  },
};
