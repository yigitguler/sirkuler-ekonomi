#!/usr/bin/env bash
# Article API – ready-to-run curl example
# 1. Set your secret: export ARTICLE_API_SECRET="your-secret"
# 2. Run: bash docs/curl_article_example.sh
# Or: curl ... -H "X-API-Key: YOUR_SECRET" ...

set -e
SECRET="${ARTICLE_API_SECRET:-YOUR_SECRET}"
URL="${ARTICLE_API_URL:-https://sirkulerekonomi.com/api/articles/}"

curl -X POST "$URL" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $SECRET" \
  -d '{
    "title": "Döngüsel Ekonomi ve Sürdürülebilir Üretim",
    "intro": "Avrupa Birliği yeşil mutabakatı ve yerel uygulamalar.",
    "meta_title": "Döngüsel Ekonomi 2025 – Sürdürülebilir Üretim",
    "meta_description": "Döngüsel ekonomi, yeşil mutabakat ve sürdürülebilir üretim uygulamaları hakkında güncel analiz.",
    "meta_keywords": "döngüsel ekonomi, sürdürülebilirlik, yeşil mutabakat",
    "publish_immediately": true,
    "body": "Sürdürülebilir büyüme ve kaynak verimliliği, günümüz sanayi politikalarının merkezinde yer alıyor. Bu yazıda **döngüsel ekonomi** modelleri ve uygulama örneklerini inceliyoruz.\n\n## Yeşil Mutabakat ve Hedefler\n\nAvrupa Birliği Yeşil Mutabakatı, 2050 karbon nötr hedefine yönelik yatırım ve düzenlemeleri içeriyor. Üye ülkeler ve ticaret ortakları için *dönüşüm* fırsatları ve yükümlülükler getiriyor.\n\nYerel üreticilerin uyum süreçleri, finansman araçları ve teknik destek programlarıyla desteklenmesi gerekiyor.\n\n### Atık Azaltımı ve Geri Kazanım\n\nAtık yönetimi ve geri dönüşüm altyapısı, döngüsel ekonominin temel taşlarından biri.\n\n> Döngüsel ekonomi, ürünlerin ve malzemelerin mümkün olduğunca uzun süre ekonomide kalmasını ve atığın en aza indirilmesini amaçlar.\n\nSonuç olarak, hem çevresel hem de ekonomik fayda sağlayan bir üretim modeli giderek daha fazla benimseniyor."
  }'
