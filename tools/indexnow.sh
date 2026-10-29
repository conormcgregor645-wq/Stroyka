#!/usr/bin/env bash
# IndexNow: сообщает Яндексу об изменённых страницах сайта.
#
#   tools/indexnow.sh <коммит-до> <коммит-после>
#
# Берёт HTML-страницы, изменённые между двумя коммитами, оставляет только те,
# что есть в sitemap.xml (служебные noindex-страницы не отправляются), ждёт,
# пока GitHub Pages опубликует коммит, и отправляет список POST-запросом на
# https://yandex.com/indexnow. Ключ — файл <ключ>.txt в корне сайта.
#
# Скрипт никогда не завершается с ошибкой: при любой проблеме он пишет
# предупреждение (::warning:: в GitHub Actions) и выходит с кодом 0.
set -u

warn() { echo "::warning::IndexNow: $*"; exit 0; }

BEFORE="${1:-}"
AFTER="${2:-HEAD}"
HOST="metrazh.online"
SITE="https://$HOST/"
ENDPOINT="https://yandex.com/indexnow"

cd "$(dirname "$0")/.." || warn "нет корня репозитория"

KEY_FILE=$(ls | grep -E '^[0-9a-f]{32}\.txt$' | head -n 1)
[ -n "$KEY_FILE" ] || warn "не найден файл ключа <ключ>.txt в корне"
KEY="${KEY_FILE%.txt}"

# Первый пуш ветки или неизвестный коммит: сравниваем с предыдущим коммитом.
if [ -z "$BEFORE" ] || ! git cat-file -e "$BEFORE^{commit}" 2>/dev/null; then
  BEFORE="$AFTER~1"
fi

CHANGED=$(git diff --name-only --diff-filter=AMR "$BEFORE" "$AFTER" -- '*.html' | grep -v '/' || true)
[ -n "$CHANGED" ] || { echo "IndexNow: изменённых HTML-страниц нет."; exit 0; }

URLS=()
for f in $CHANGED; do
  if [ "$f" = "index.html" ]; then url="$SITE"; else url="$SITE$f"; fi
  if grep -q "<loc>$url</loc>" sitemap.xml; then URLS+=("$url"); fi
done
[ "${#URLS[@]}" -gt 0 ] || { echo "IndexNow: изменились только страницы вне sitemap — отправлять нечего."; exit 0; }
printf 'IndexNow: страницы к отправке:\n'; printf '  %s\n' "${URLS[@]}"

# Ждём публикации коммита на GitHub Pages (до 10 минут), иначе робот увидит старую версию.
SHA=$(git rev-parse "$AFTER")
if [ -n "${GH_TOKEN:-}" ] && [ -n "${GITHUB_REPOSITORY:-}" ]; then
  for _ in $(seq 1 40); do
    build=$(gh api "repos/$GITHUB_REPOSITORY/pages/builds/latest" --jq '.status + " " + .commit' 2>/dev/null || true)
    if [ "$build" = "built $SHA" ]; then echo "IndexNow: Pages опубликовал $SHA."; break; fi
    sleep 15
  done
  [ "$build" = "built $SHA" ] || echo "::warning::IndexNow: не дождался публикации $SHA на Pages (последняя сборка: ${build:-нет данных}), отправляю как есть."
fi

LIST=$(printf '"%s",' "${URLS[@]}")
BODY="{\"host\":\"$HOST\",\"key\":\"$KEY\",\"keyLocation\":\"$SITE$KEY_FILE\",\"urlList\":[${LIST%,}]}"

CODE=$(curl -sS -o /tmp/indexnow-response.txt -w '%{http_code}' --max-time 30 \
  -H 'Content-Type: application/json; charset=utf-8' -X POST --data "$BODY" "$ENDPOINT") || warn "запрос не выполнен (сеть)"
case "$CODE" in
  200|202) echo "IndexNow: Яндекс принял ${#URLS[@]} адрес(ов), ответ $CODE." ;;
  *) warn "Яндекс ответил $CODE: $(head -c 300 /tmp/indexnow-response.txt 2>/dev/null)" ;;
esac
exit 0
