#!/bin/bash
# Fetch Shan Hai Jing (山海经) from ctext.org
# Usage: ./fetch_shanjing.sh [data_dir]

set -euo pipefail

DATA_DIR="${1:-./shanhaijing}"
mkdir -p "$DATA_DIR"

# 18 chapters of Shan Hai Jing
CHAPTERS=(
    "nan-shan-jing|南山经|Nan Shan Jing (Classic of the Southern Mountains)"
    "xi-shan-jing|西山经|Xi Shan Jing (Classic of the Western Mountains)"
    "bei-shan-jing|北山经|Bei Shan Jing (Classic of the Northern Mountains)"
    "dong-shan-jing|东山经|Dong Shan Jing (Classic of the Eastern Mountains)"
    "zhong-shan-jing|中山经|Zhong Shan Jing (Classic of the Central Mountains)"
    "hai-wai-nan-jing|海外南经|Hai Wai Nan Jing (Classic of Regions Beyond the Seas: South)"
    "hai-wai-xi-jing|海外西经|Hai Wai Xi Jing (Classic of Regions Beyond the Seas: West)"
    "hai-wai-dong-jing|海外东经|Hai Wai Dong Jing (Classic of Regions Beyond the Seas: East)"
    "hai-wai-bei-jing|海外北经|Hai Wai Bei Jing (Classic of Regions Beyond the Seas: North)"
    "hai-nei-nan-jing|海内南经|Hai Nei Nan Jing (Classic of Regions Within the Seas: South)"
    "hai-nei-xi-jing|海内西经|Hai Nei Xi Jing (Classic of Regions Within the Seas: West)"
    "hai-nei-dong-jing|海内东经|Hai Nei Dong Jing (Classic of Regions Within the Seas: East)"
    "hai-nei-bei-jing|海内北经|Hai Nei Bei Jing (Classic of Regions Within the Seas: North)"
    "da-huang-dong-jing|大荒东经|Da Huang Dong Jing (Classic of the Great Wilderness: East)"
    "da-huang-nan-jing|大荒南经|Da Huang Nan Jing (Classic of the Great Wilderness: South)"
    "da-huang-xi-jing|大荒西经|Da Huang Xi Jing (Classic of the Great Wilderness: West)"
    "da-huang-bei-jing|大荒北经|Da Huang Bei Jing (Classic of the Great Wilderness: North)"
    "hai-nei-jing|海内经|Hai Nei Jing (Classic of Regions Within the Seas)"
)

UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

for entry in "${CHAPTERS[@]}"; do
    IFS='|' read -r slug name_cn name_en <<< "$entry"
    echo "========================================="
    echo "Fetching: $name_cn / $name_en"
    echo "Slug: $slug"
    echo "========================================="

    # Fetch Chinese version
    echo "  -> Chinese version..."
    curl -s -L \
        -H "User-Agent: $UA" \
        -H "Accept: text/html,application/xhtml+xml" \
        -H "Accept-Language: zh-CN,zh;q=0.9" \
        "https://ctext.org/shan-hai-jing/$slug/zhs" \
        > "$DATA_DIR/${slug}_zh_raw.html"
    sleep 2

    # Fetch English version
    echo "  -> English version..."
    curl -s -L \
        -H "User-Agent: $UA" \
        -H "Accept: text/html,application/xhtml+xml" \
        -H "Accept-Language: en-US,en;q=0.9" \
        "https://ctext.org/shan-hai-jing/$slug/ens" \
        > "$DATA_DIR/${slug}_en_raw.html"
    sleep 2

    echo "  -> Done."
done

echo ""
echo "All chapters fetched. Files saved in: $DATA_DIR/"
ls -la "$DATA_DIR/"
