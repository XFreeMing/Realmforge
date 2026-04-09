# Realmforge（铸造世界）— Unified Economy, Attribute & Photo Pipeline Design

> Reconciles DESIGN.md, beast_and_combat_design.md, technical-architecture.md, and DESIGN_WORLD_LORE.md into a single consistent system.

---

## Table of Contents

1. [Unified Material Economy](#1-unified-material-economy)
2. [Unified Attribute System](#2-unified-attribute-system)
3. [Photo Pipeline Decision Logic](#3-photo-pipeline-decision-logic)
4. [Cross-System Mapping Tables](#4-cross-system-mapping-tables)

---

## 1. Unified Material Economy

### 1.1 The Three Source Channels

All materials in Realmforge come from exactly three sources. The source determines the material's *acquisition context* but the resulting material uses the same unified data model:

| Source | Channel Name | How It Works |
|--------|-------------|--------------|
| **Photo Capture** | 万象镜摄 (Mirror Capture) | Photograph real-world objects → essence extraction → material |
| **Beast Encounter** | 灵兽馈赠 (Beast Gift) | Pacify or defeat beasts → they drop materials |
| **Realm Discovery** | 秘境探得 (Realm Find) | Explore world locations, solve puzzles, restore faded fragments → discover materials in situ |

### 1.2 Unified Material Data Model

Every material in the game conforms to this single schema:

```
Material
├── id: UUID
├── template_id: UUID (references MaterialTemplate)
├── name_cn: string            # e.g. "玄铁碎片", "青木灵叶"
├── name_en: string            # e.g. "Dark Iron Fragment", "Azure Spirit Leaf"
├── essence_type: enum         # 金灵/木灵/水灵/火灵/土灵/生灵/丝灵/玉灵 (see 1.3)
├── drop_tier: int             # T1-T5 (see 1.4)
├── rarity_weight: int         # Common 60 / Uncommon 25 / Rare 10 / Epic 4 / Legendary 1
├── quality_grade: enum        # 完美/精良/普通/粗糙 (photo source only; others default 普通)
├── properties: JSONB
│   ├── hardness: int (1-10)       # physical resistance
│   ├── flexibility: int (1-10)    # bend without breaking
│   ├── density: int (1-10)        # weight class
│   ├── conductivity: int (1-10)   # energy/magic channeling
│   └── shanhai_origin: string     # e.g. "南山经", "海外东经"
├── element: enum              # 金/木/水/火/土 (for 五行 calculations)
├── magic_affinity: int (1-10) # innate magical potency
├── source: enum               # mirror_capture / beast_gift / realm_find
├── source_detail: JSONB       # { photo_object: "leaf", beast_id: "uuid", location: "forge_valley" }
└── codex_entry_id: UUID       # links to the 博物志 entry
```

### 1.3 Unified Essence Type System (八灵 — Eight Essences)

The five 五行 elements from DESIGN.md map directly to the 五灵 from DESIGN_WORLD_LORE.md. We add three more categories to cover the bonus categories (Silk, Gem) and the living-creature captures:

| Essence | Chinese | 五行 | Color Theme | Real-World Sources | Beast Drop Example | Realm Find Example |
|---------|---------|------|-------------|-------------------|-------------------|-------------------|
| **金灵** (Metal) | 金灵 | 金 | Silver/Gold | Coins, keys, tools, foil | 玄铁碎 (Dark Iron Shard) from Metal-type beasts | 矿脉精晶 from 熔炉谷 |
| **木灵** (Wood) | 木灵 | 木 | Green/Brown | Leaves, twigs, paper, cardboard | 建木芯 (Jianmu Core) from Forest beasts | 百草园灵根 |
| **水灵** (Water) | 水灵 | 水 | Blue/Teal | Water drops, ice, shells, glass | 鲛人泪 (Merfolk Tear) from Sea beasts | 归墟寒晶 |
| **火灵** (Fire) | 火灵 | 火 | Red/Orange | Candles, warm-colored items, red objects | 祝融火种 (Zhurong Ember) from Fire beasts | 雷池焰心 |
| **土灵** (Earth) | 土灵 | 土 | Brown/Yellow | Rocks, soil, sand, ceramics, pottery | 息壤块 (Living Soil) from Mountain beasts | 不周山星岩 |
| **生灵** (Living) | 生灵 | — | Multicolor | Animals, insects, pets | 九尾狐毛 (Nine-Tail Fur) — direct beast drops | 梦境生灵露 |
| **丝灵** (Silk) | 丝灵 | — | White/Pink | Fabric, thread, cotton, wool, web | 云蚕丝 (Cloud-Silk) from Silk-producing beasts | 织女遗锦 |
| **玉灵** (Gem) | 玉灵 | — | Purple/Crystal | Glass, gems, clear plastic, beads | 和氏璧碎片 (Heshi Jade) from Treasure beasts | 龙宫遗玉 |

**Reconciliation note:** DESIGN.md listed "Silk" and "Gem" as bonus categories outside 五行. DESIGN_WORLD_LORE.md listed 生灵 (living essence) as a special capture type. We promote all three to full essence types, giving us eight total. The core five remain 五行 for synergy calculations; the extra three participate in crafting but do not count toward 五行 cycle completion.

### 1.4 Unified Rarity Scale (五级品阶)

A single rarity scale serves both photo captures and beast drops. The same tier names and probabilities are used everywhere:

| Tier | Chinese | Stars | Photo Probability | Beast Drop Probability | Realm Find Probability | Drop Tier Range |
|------|---------|-------|-------------------|----------------------|----------------------|-----------------|
| **Common** | 凡品 | ★ | 60% | T1 guaranteed, T2 at 40% | T1-T2 | T1 |
| **Uncommon** | 灵品 | ★★ | 25% | T2 guaranteed, T3 at 25% | T2-T3 | T1-T2 |
| **Rare** | 珍品 | ★★★ | 10% | T3 guaranteed, T4 at 10% | T3-T4 | T2-T3 |
| **Epic** | 神品 | ★★★★ | 4% | T4 guaranteed, T5 at 3% | T4-T5 | T3-T4 |
| **Legendary** | 仙品 | ★★★★★ | 1% | T5 guaranteed at 0.5% | T5 at 1% | T4-T5 |

**How the two old systems map:**

```
Old DESIGN.md rarity     →  Unified rarity
  Common (60%)           →  凡品 (Common)  ★
  Uncommon (25%)         →  灵品 (Uncommon)  ★★
  Rare (10%)             →  珍品 (Rare)  ★★★
  Epic (4%)              →  神品 (Epic)  ★★★★
  Legendary (1%)         →  仙品 (Legendary)  ★★★★★

Old beast drop tier      →  Unified drop tier
  T1 凡材                →  T1 (凡品-灵品 range)
  T2 灵材                →  T2 (灵品-珍品 range)
  T3 宝材                →  T3 (珍品-神品 range)
  T4 神材                →  T4 (神品-仙品 range)
  T5 仙材                →  T5 (仙品 only)

Old mutation rarity      →  Unified rarity (same scale, reused)
  N 普通 (60%)           →  凡品
  R 稀有 (25%)           →  灵品
  SR 精英 (10%)          →  珍品
  SSR 传说 (4%)          →  神品
  UR 神话 (1%)           →  仙品
```

**All three systems now share the exact same 60/25/10/4/1 distribution.** This makes the economy predictable, teachable, and easy to balance.

### 1.5 Material Sinks (What Consumes Materials)

Besides weapon crafting, materials are consumed by:

| Sink | What It Consumes | What It Produces | Frequency |
|------|-----------------|------------------|-----------|
| **Weapon/Tool Crafting** | 3-5 materials of varying tiers | Forged equipment | Core loop |
| **Beast Feeding** | T1-T2 materials matching beast element | Beast XP, bond increase | Per-session |
| **Beast Breeding/Fusion** | T2-T3 materials as "catalysts" | New beast with inherited mutations | Occasional |
| **Beast Mutation Transfer** | T3 基因碎片 + matching element material | Move mutation between beasts | Rare |
| **Realm Restoration** | 5-10 materials of specific essence types | Restore faded realm fragment, unlock area | Story progression |
| **Recipe Discovery** | 2 materials combined experimentally | Unlock new recipe in codex | Exploration |
| **Forge Mini-Game Buffs** | T1 consumable materials (burn during forging) | +5-15% forge quality multiplier | Per-forge |
| **Elemental Trial Puzzles** | Materials matching puzzle element | Knowledge items, rare rewards | Puzzle encounters |
| **Festival Crafting** | Seasonal + regular materials | Limited-time cosmetics/items | Seasonal events |
| **Mirror Upgrade** | T3+ materials of all five 五行 elements | Increase mirror resonance level | Milestone |

### 1.6 Inventory Limits (Child-Appropriate)

| Slot Type | Cap | Rationale |
|-----------|-----|-----------|
| **Material Inventory** | 100 total slots | Prevents hoarding; encourages crafting. Expands to 150 at mirror level 5, 200 at level 10. |
| **Per-Stack Limit** | 99 of same material | Prevents single-material overflow; teaches stack management. |
| **Equipment Inventory** | 20 forged items | Encourages using old weapons or storing them in the "forge museum." |
| **Beast Roster** | 8 active beasts + 12 in sanctuary | Manageable number for children. Sanctuary expands with bond level. |
| **T5 Material Cap** | 5 per type | Ultra-rare materials have hard caps to maintain scarcity and specialness. |
| **Consumable Stack** | 20 per type | Forge buffs, potions, etc. |

**Overflow behavior:** When inventory is full, the game gently prompts: "Your pack is full! Visit the forge to use some materials, or store extras in your village chest." No materials are ever lost.

### 1.7 Currency System: 灵魄 (Spirit Shards)

Realmforge uses a **single, soft currency** with no real-money purchases:

| Property | Detail |
|----------|--------|
| **Name** | 灵魄 (Lingpo / Spirit Shard) |
| **Icon** | Glowing crystal shard |
| **Earned From** | Combat pacification (5-20), realm restoration (50-200), daily exploration bonus (10), codex completion bonus (25-100) |
| **Spent On** | Forge repair (5-15 per repair), mirror resonance upgrades (100-500), beast sanctuary expansion (200), recipe hints from NPCs (10-30) |
| **NOT Spent On** | Materials, beasts, equipment — these must all be earned through gameplay |
| **Soft Cap** | 9999 (displayed as "9999+" if exceeded; no hard stop) |
| **No Real-Money Transactions** | Spirit Shards cannot be purchased. This is a design principle for a children's game. |

**Economy flow diagram:**

```
                ┌──────────────┐
                │  Photo Capture│
                └──────┬───────┘
                       │ materials
                       ▼
┌──────────┐    ┌──────────────┐    ┌───────────────┐
│ Beasts    │───→│   Materials   │───→│  Crafting     │
│ (drops)   │    │  (inventory)  │    │  (weapons)    │
└──────────┘    └──────┬───────┘    └───────┬───────┘
                       │                    │
                       ▼                    ▼
               ┌──────────────┐    ┌───────────────┐
               │ Beast Feeding│    │ Combat/Explore│
               │ Breeding     │    │ → Spirit Shards│
               │ Restoration  │    └───────┬───────┘
               └──────────────┘            │
                                           │ spent on
                                           ▼
                                   ┌───────────────┐
                                   │ Upgrades &    │
                                   │ Repairs       │
                                   └───────────────┘
```

---

## 2. Unified Attribute System

### 2.1 Reconciliation of Conflicting Attribute Lists

**DESIGN.md (7 attributes):** Attack, Defense, Speed, Durability, Magic Power, Balance, Harmony

**technical-architecture.md (6 attributes):** Attack, Defense, Speed, Spirit (灵力), Element (元素), Special Effects (特效)

**Reconciliation decision:** We use **6 primary attributes** displayed to the player, with Durability and Harmony as hidden meta-attributes. The Element attribute becomes part of the display as a tag rather than a numeric stat. Special Effects remain as bonus text.

| # | Attribute | Chinese | Icon | Old DESIGN.md | Old tech-arch | Source |
|---|-----------|---------|------|---------------|---------------|--------|
| 1 | **Power** | 力道 | ⚔️ | Attack | Attack | Shape sharpness + material hardness |
| 2 | **Guard** | 守护 | 🛡️ | Defense | Defense | Shape area + material density |
| 3 | **Swiftness** | 灵动 | ⚡ | Speed | Speed | Shape symmetry + material flexibility |
| 4 | **Spirit** | 灵力 | 🔮 | Magic Power | Spirit | Shape complexity + material conductivity |
| 5 | **Steady** | 稳健 | ⚖️ | Balance | — | Shape symmetry + center of mass (hidden from combat, shown in forge report) |
| 6 | **Element** | 五行 | 🌀 | — | Element | Material element + drawing color (displayed as element tag, not a number) |

**What happened to the old attributes:**

| Old Attribute | Where It Went |
|---------------|---------------|
| Durability (DESIGN.md) | Becomes a **hidden equipment property** (not a combat stat). Weapons degrade over uses; durability is calculated from material hardness + flexibility. Shown only in the equipment detail screen as a "health bar" for the weapon. |
| Harmony (DESIGN.md) | Becomes the **forge synergy score** — a hidden multiplier applied during crafting. Displayed during the forge screen as a 五行 compatibility meter (good/neutral/poor). Not a weapon stat. |
| Special Effects (tech-arch) | Becomes **bonus text** on the weapon card (e.g., "蒸汽爆发: Water+Fire combination"). Derived from material combinations. Not a numeric stat. |

### 2.2 Canonical Attribute List (Final)

The weapon card shows exactly these to the child:

```
┌─────────────────────────────────┐
│  赤焰剑 (Crimson Flame Sword)    │
│                                 │
│  ⚔️ 力道 Power:      ██████░░░░ 62 │
│  🛡️ 守护 Guard:      ████░░░░░░ 38 │
│  ⚡ 灵动 Swiftness:  █████░░░░░ 50 │
│  🔮 灵力 Spirit:     ███░░░░░░░ 28 │
│                                 │
│  🌀 五行: 火 (Fire)              │
│  ✨ 特效: 炎击 (Flame Strike)    │
│                                 │
│  ⚖️ 稳健: 72 (hidden, shown on  │
│     detail screen only)         │
└─────────────────────────────────┘
```

**Age-appropriate names and explanations:**

| Attribute | Child-Friendly Name | Explanation to Child |
|-----------|-------------------|---------------------|
| Power (力道) | "有多猛！" | "How hard it hits!" |
| Guard (守护) | "有多稳！" | "How well it blocks!" |
| Swiftness (灵动) | "有多快！" | "How quick it moves!" |
| Spirit (灵力) | "有多玄！" | "How much magic it channels!" |
| Steady (稳健) | "有多顺手！" | "How easy it is to control!" |

### 2.3 Attribute Calculation Pipeline

Every attribute is computed from three inputs: **shape analysis**, **material properties**, and **五行 synergy**.

```
┌──────────────────────────────────────────────────────────────────┐
│                    Attribute Calculation Pipeline                 │
│                                                                  │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────┐      │
│  │ Shape       │   │ Materials    │   │ 五行 Synergy     │      │
│  │ Analysis    │   │ Properties   │   │                  │      │
│  │             │   │              │   │  [element list]  │      │
│  │ sharpness   │   │ hardness     │   │  → gen/dest map  │      │
│  │ area        │   │ flexibility  │   │  → bonus/penalty │      │
│  │ symmetry    │   │ density      │   │                  │      │
│  │ complexity  │   │ conductivity │   │                  │      │
│  │ center_mass │   │ element      │   │                  │      │
│  └──────┬──────┘   └──────┬───────┘   └────────┬─────────┘      │
│         │                 │                     │                │
│         └─────────────────┼─────────────────────┘                │
│                           ▼                                      │
│              ┌────────────────────────┐                          │
│              │  Weighted Combination  │                          │
│              │                        │                          │
│              │  attr = f(shape, mat,  │                          │
│              │         synergy, q)    │                          │
│              │                        │                          │
│              │  q = quality multiplier│                          │
│              │    (photo: 0.95-1.20)  │                          │
│              │    (forge: 0.90-1.30)  │                          │
│              └───────────┬────────────┘                          │
│                          │                                       │
│                          ▼                                       │
│              ┌────────────────────────┐                          │
│              │  Clamp to 1-100        │                          │
│              │  Round to integer      │                          │
│              └────────────────────────┘                          │
└──────────────────────────────────────────────────────────────────┘
```

### 2.4 Exact Calculation Formulas

Each attribute uses a weighted sum of shape features and material properties, modified by synergy and quality:

```python
# Shape features (0.0-1.0 normalized):
#   sharpness     = sharp_points_count / max(1, total_strokes)
#   area_ratio    = enclosed_pixel_area / bounding_box_area
#   symmetry      = 1.0 - left_right_pixel_difference / total_pixels
#   complexity    = unique_color_count / max_color_count
#   center_offset = distance(center_of_mass, geometric_center) / max_distance

# Material properties (1-10 scale):
#   hardness, flexibility, density, conductivity

# Quality multiplier:
#   Photo: Flawless=1.20, Fine=1.10, Normal=1.00, Rough=0.95
#   Forge mini-game: Perfect(90%+)=1.30, Great(70-89%)=1.15,
#                     Good(50-69%)=1.00, Rough(<50%)=0.90

def calculate_attributes(shape, materials, forge_quality):
    n = len(materials)

    # Average material properties
    avg_hardness     = sum(m.hardness     for m in materials) / n
    avg_flexibility  = sum(m.flexibility  for m in materials) / n
    avg_density      = sum(m.density      for m in materials) / n
    avg_conductivity = sum(m.conductivity for m in materials) / n

    # Quality multiplier (photo quality × forge quality)
    quality_mult = shape.photo_quality_mult * forge_quality

    # 五行 synergy bonus (see 2.5)
    synergy = calculate_wuxing_synergy([m.element for m in materials])

    # Base formulas (raw 0-100 range before clamping)
    power     = (shape.sharpness * 50 + avg_hardness * 4 + avg_density * 1) * (1 + synergy)
    guard     = (shape.area_ratio * 60 + avg_hardness * 2 + avg_density * 2) * (1 + synergy)
    swiftness = (shape.symmetry * 40 + avg_flexibility * 4 + (10 - avg_density) * 2) * (1 + synergy)
    spirit    = (shape.complexity * 30 + avg_conductivity * 5) * (1 + synergy)
    steady    = (shape.symmetry * 60 + (1 - shape.center_offset) * 40)

    # Apply quality multiplier
    power     = clamp(power * quality_mult)
    guard     = clamp(guard * quality_multiplier)
    swiftness = clamp(swiftness * quality_mult)
    spirit    = clamp(spirit * quality_mult)
    steady    = clamp(steady * quality_mult)

    # Element: most common material element (ties broken by highest conductivity)
    element = dominant_element(materials)

    # Special effects: detected from material combinations
    effects = detect_special_effects(materials)

    return {
        "power": power, "guard": guard, "swiftness": swiftness,
        "spirit": spirit, "steady": steady,
        "element": element, "special_effects": effects
    }

def clamp(value, lo=1, hi=100):
    return max(lo, min(hi, int(round(value))))
```

### 2.5 五行 Synergy Calculation (Unified)

| Combination | Chinese | Synergy | Effect |
|-------------|---------|---------|--------|
| All 5 五行 elements present | 五行俱全 | +50% | Maximum bonus to all attributes |
| 3+ elements in generative chain (相生) | 相生流转 | +30% | Strong bonus |
| 2 elements in generative relationship | 相生 | +15% | Moderate bonus |
| 2 elements in destructive relationship | 相克 | -10% + unlock special effect | Penalty but unique ability |
| Same element repeated (3+) | 专精 | +20% to that element's attribute, -10% to others | Specialized weapon |
| All same element (5 slots) | 极致 | +40% to one attribute, -20% to all others | Extreme weapon |

**Generative chain (相生):** 木 → 火 → 土 → 金 → 水 → 木

**Destructive chain (相克):** 木 → 土 → 水 → 火 → 金 → 木

### 2.6 Attribute-to-Combat Mapping

How weapon attributes affect combat:

| Weapon Attribute | Combat Effect |
|-----------------|---------------|
| Power (力道) | Base damage multiplier on Attack action |
| Guard (守护) | Damage reduction when using Defend action (Guard% / 100 × block effectiveness) |
| Swiftness (灵动) | Timing window width for mini-games (+Swiftness% wider windows) |
| Spirit (灵力) | Elemental attack damage multiplier; determines strength of Special Effects |
| Steady (稳健) | Reduces "miss" penalty in mini-games (higher steady = more forgiving) |
| Element (五行) | Determines attack element; interacts with beast element via 五行相克 (200% vs weak, 50% vs strong) |
| Special Effects | Triggers on hit with probability = Spirit / 200 (e.g., Flame Strike: 20% chance at Spirit=40) |

### 2.7 How Each Attribute Is Calculated from Each Input Source

| Attribute | From Shape (Drawing) | From Material Properties | From 五行 |
|-----------|---------------------|-------------------------|-----------|
| **Power** | Sharp points count, stroke angularity | Hardness (60%), Density (40%) | Synergy multiplier |
| **Guard** | Enclosed area ratio, perimeter | Hardness (40%), Density (30%), Flexibility (30%) | Synergy multiplier |
| **Swiftness** | Symmetry score, stroke count (fewer = faster) | Flexibility (50%), inverse Density (50%) | Synergy multiplier |
| **Spirit** | Stroke complexity, color variety | Conductivity (100%) | Synergy multiplier |
| **Steady** | Symmetry (60%), center of mass alignment (40%) | — (pure shape) | — |
| **Element** | Dominant drawing color | Most common material element | Determined by material majority |

**Color-to-element mapping (from drawing):**

| Dominant Color | Element |
|---------------|---------|
| Red/Orange | 火 (Fire) |
| Blue/Teal | 水 (Water) |
| Green | 木 (Wood) |
| Yellow/Brown | 土 (Earth) |
| White/Silver/Gold | 金 (Metal) |
| Purple | Bonus: adds +5 Spirit |
| Black | Bonus: adds +5 Power |

When drawing color and material element disagree, material element takes priority (70% weight) but drawing color shifts the element slightly (30% weight), creating "dual-element" weapons when the two are adjacent in the generative chain.

---

## 3. Photo Pipeline Decision Logic

### 3.1 The Single Decision Tree

When a child photographs something, the system runs through this exact decision tree:

```
Photo Captured
     │
     ▼
┌─────────────────────────────┐
│ Step 1: Content Analysis     │
│ - Object classification      │
│   (MobileNetV4 / CLIP)       │
│ - Living vs non-living check │
│ - Essence type assignment    │
│   (八灵 from 1.3)            │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Step 2: Primary Outcome      │
│                              │
│ IF living_thing (animal,     │
│    insect, pet):             │
│   → BEAST ENCOUNTER         │
│                              │
│ IF drawing/artwork:          │
│   → BEAST (animated drawing)│
│                              │
│ IF weather/natural event     │
│    (rainbow, sunset, snow):  │
│   → REALM UNLOCK + material │
│                              │
│ IF object (everything else): │
│   → MATERIAL                 │
│   + chance for recipe       │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Step 3: Secondary Bonuses    │
│ (always checked, independent │
│  of primary outcome)         │
│                              │
│ - 10% chance: Recipe         │
│   discovery                  │
│ - 5% chance: Realm key       │
│   fragment                   │
│ - Mirror XP always awarded   │
│ - Codex entry if new type    │
└──────────────────────────────┘
```

### 3.2 Exact Outcome Probabilities by Input Type

| Input Type | Primary Outcome | Probability | Secondary Bonuses |
|------------|----------------|-------------|-------------------|
| **Object (non-living)** | Material (essence based on object class) | 100% | 10% recipe, 5% realm key |
| **Living animal/insect** | Beast encounter spawn | 80% | 15% material drop instead, 5% realm key |
| **Pet (recognized pet breed)** | Beast encounter (personalized) | 90% | 10% material drop |
| **Child's drawing** | Animated beast from drawing | 100% | 10% bonus recipe |
| **Food** | Beast (food spirit) or Material (ingredient essence) | 60% beast / 40% material | 10% recipe |
| **Weather/natural event** | Realm unlock fragment + T2-T3 material | 100% | 15% additional material |
| **Landscape/park** | New world zone inspiration + T2-T3 materials | 100% | 20% recipe discovery |

### 3.3 Essence Type Reconciliation (DESIGN.md vs DESIGN_WORLD_LORE.md)

The two classification systems are reconciled into a single mapping table:

| Real-World Object Class | DESIGN.md Category | DESIGN_WORLD_LORE 五灵 | Unified Essence | Typical Outcome |
|------------------------|-------------------|----------------------|-----------------|-----------------|
| Coins, keys, tools, foil, electronics | Metal | 金灵 | 金灵 (Metal) | Material (T1-T2) |
| Leaves, flowers, bark, paper, wood | Wood | 木灵 | 木灵 (Wood) | Material (T1-T2) |
| Water, ice, mirrors, glass, shells | Water | 水灵 | 水灵 (Water) | Material (T1-T2) |
| Candles, warm items, red objects, sunlight | Fire | 火灵 | 火灵 (Fire) | Material (T1-T2) |
| Rocks, soil, sand, pottery, bricks | Earth | 土灵 | 土灵 (Earth) | Material (T1-T2) |
| Fabric, thread, cotton, wool, clothing | Silk (bonus) | — | 丝灵 (Silk) | Material (T1-T3) |
| Glass beads, gems, crystals, jewelry | Gem (bonus) | — | 玉灵 (Gem) | Material (T2-T3) |
| Animals, insects, pets | — | 生灵 | 生灵 (Living) | Beast encounter (80%) |
| Drawings, toys, crafts | — | 人灵 | 生灵 (Living) | Beast from drawing (100%) |
| Rain, snow, rainbow, clouds | — | 天气灵 | Fire or Water + Realm key | Material + realm unlock |

### 3.4 Rarity Determination for Photo Captures

The rarity of a photo-captured material is determined by three factors:

```
Rarity Score = Object Rarity Weight + Photo Quality Weight + Mirror Level Weight

Object Rarity Weight (based on ML classification confidence + object class):
  Everyday objects (leaf, paper, pebble):         weight 0-30
  Somewhat interesting (fabric, shell, flower):   weight 30-60
  Interesting (key, coin, feather):               weight 60-80
  Rare objects (crystal, unique specimen):         weight 80-95
  Exceptional (identified by cloud AI):            weight 95-100

Photo Quality Weight:
  Flawless (clear, well-lit, fills frame):        +10
  Fine (good photo):                              +5
  Normal (average):                               +0
  Rough (blurry, dark):                           -5

Mirror Level Weight:
  Mirror level 1-3:   +0
  Mirror level 4-6:   +5
  Mirror level 7-9:   +10
  Mirror level 10:    +15

Final Rarity Determination:
  Score 0-30:    凡品 (Common)     ★
  Score 31-55:   灵品 (Uncommon)   ★★
  Score 56-75:   珍品 (Rare)       ★★★
  Score 76-90:   神品 (Epic)       ★★★★
  Score 91+:     仙品 (Legendary)   ★★★★★
```

**Important:** The base probabilities (60/25/10/4/1) are enforced globally across all captures over time. Individual captures use the scoring system above, but the overall distribution is calibrated so that the long-term average matches the target probabilities. This prevents a child from getting streaks of legendary items early on, while still allowing genuinely exceptional captures to break through.

### 3.5 Photo Pipeline Flow Diagram

```
                    REAL WORLD
                         │
                    [Camera]
                         │
                         ▼
               ┌─────────────────────┐
               │  Content Analysis    │
               │  ┌───────────────┐  │
               │  │ Classification │  │
               │  │ (on-device ML) │  │
               │  └───────┬───────┘  │
               │          │          │
               │  ┌───────▼───────┐  │
               │  │ Essence Type  │  │
               │  │ (八灵 mapping) │  │
               │  └───────┬───────┘  │
               │          │          │
               │  ┌───────▼───────┐  │
               │  │ Rarity Score  │  │
               │  │ (object+photo │  │
               │  │  +mirror lvl) │  │
               │  └───────┬───────┘  │
               └──────────┼──────────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
              ▼           ▼           ▼
         ┌─────────┐ ┌────────┐ ┌──────────┐
         │Material │ │ Beast  │ │ Realm    │
         │(object) │ │(living)│ │(weather) │
         └────┬────┘ └───┬────┘ └────┬─────┘
              │          │           │
              └──────────┼───────────┘
                         │
                         ▼
               ┌─────────────────────┐
               │  Secondary Checks   │
               │  - Recipe? (10%)    │
               │  - Realm key? (5%)  │
               │  - Codex new entry? │
               │  - Mirror XP        │
               └─────────────────────┘
```

---

## 4. Cross-System Mapping Tables

### 4.1 Material Template: Complete Property Table

Every material template has these properties. The values below show the typical ranges for each essence type at T1 (Common):

| Property | 金灵 (Metal) | 木灵 (Wood) | 水灵 (Water) | 火灵 (Fire) | 土灵 (Earth) | 丝灵 (Silk) | 玉灵 (Gem) | 生灵 (Living) |
|----------|-------------|-------------|-------------|-------------|-------------|-------------|------------|---------------|
| hardness | 7-9 | 2-4 | 3-5 | 4-6 | 6-8 | 2-3 | 7-10 | 3-5 |
| flexibility | 3-5 | 6-8 | 5-7 | 4-6 | 2-4 | 7-9 | 2-4 | 6-8 |
| density | 8-10 | 3-5 | 4-6 | 3-5 | 7-9 | 2-4 | 6-8 | 4-6 |
| conductivity | 6-8 | 4-6 | 7-9 | 8-10 | 3-5 | 5-7 | 8-10 | 6-8 |
| magic_affinity | 5-7 | 6-8 | 7-9 | 8-10 | 4-6 | 7-9 | 9-10 | 8-10 |
| Primary stat boost | Power | Swiftness | Spirit | Spirit | Guard | Swiftness | Power | Spirit |

### 4.2 Beast Drop Table by Beast Rarity

The beast's mutation rarity determines its drop tier range:

| Beast Mutation Tier | Drop Tier Range | Guaranteed Drops | Rare Drop Chance |
|--------------------|-----------------|-----------------|-----------------|
| N (凡品) | T1 only | 1-3 × T1 material | 5% T2 |
| R (灵品) | T1-T2 | 1-3 × T1, 1 × T2 | 15% T3 |
| SR (珍品) | T2-T3 | 1-3 × T2, 1 × T3 | 10% T4 |
| SSR (神品) | T3-T4 | 1-2 × T3, 1 × T4 | 5% T5 |
| UR (仙品) | T4-T5 | 1 × T4, 1 × T5 | Guaranteed T5 |

### 4.3 Essence Type to Realm Mapping

| Essence | Primary Realm | Secondary Realm | Realm Unlock Effect |
|---------|--------------|-----------------|-------------------|
| 金灵 (Metal) | 山境 (Mountain) | 云境 (Cloud) | Unlocks mineral veins, forge upgrades |
| 木灵 (Wood) | 林境 (Forest) | 山境 (Mountain) | Unlocks herbal gardens, beast habitats |
| 水灵 (Water) | 海境 (Sea) | 梦境 (Dream) | Unlocks underwater areas, crystal caves |
| 火灵 (Fire) | 云境 (Cloud) | 山境 (Mountain) | Unlocks weather crafting, forge boosters |
| 土灵 (Earth) | 山境 (Mountain) | 林境 (Forest) | Unlocks earthworks, stone puzzles |
| 生灵 (Living) | 林境 (Forest) | 梦境 (Dream) | Unlocks beast encounters, breeding grounds |
| 丝灵 (Silk) | 梦境 (Dream) | 林境 (Forest) | Unlocks special recipes, cosmetic items |
| 玉灵 (Gem) | 海境 (Sea) | 梦境 (Dream) | Unlocks puzzle chambers, advanced enchantments |

### 4.4 Summary of All Reconciliations

| Conflict Area | DESIGN.md | tech-architecture.md | beast_and_combat.md | WORLD_LORE.md | **UNIFIED** |
|--------------|-----------|---------------------|-------------------|---------------|-------------|
| **Material categories** | 五行 + Silk + Gem (7) | 五行 + 9 extended elements | Drop tiers T1-T5 | 五灵 + 生灵/人灵/天气灵 | **八灵 (8 essences)** — 5 五行 + 3 bonus |
| **Rarity tiers** | Common/Uncommon/Rare/Epic/Legendary (60/25/10/4/1) | Same enum | N/R/SR/SSR/UR (60/25/10/4/1) | 凡/奇/珍/神 (4 tiers) | **五级品阶** — 凡/灵/珍/神/仙 (60/25/10/4/1) |
| **Weapon attributes** | 7 stats (Atk/Def/Spd/Dur/Magic/Bal/Harm) | 6 stats (Atk/Def/Spd/Spirit/Element/Effects) | Combat stats | — | **6 stats** — Power/Guard/Swiftness/Spirit/Steady/Element; Durability & Harmony become meta-properties |
| **Material properties** | Hardness/Flexibility/Density/Conductivity | Hardness/Weight/Element/Shanhai/MagicAffinity | — | — | **6 properties** — Hardness/Flexibility/Density/Conductivity/Element/MagicAffinity; Weight derived from Density |
| **Photo outcomes** | Material only | Material + Beast | Beast + Material | Material + Beast + Realm + Recipe | **Decision tree** — living→beast, object→material, weather→realm, with secondary bonus rolls |
| **Currency** | None specified | None specified | No real-money trades | None | **灵魄 (Spirit Shards)** — single soft currency, no RMT |

---

*Document version: 1.0 | Realmforge Design Team | 2026-04-09*
