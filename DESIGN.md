# Realmforge (铸造世界) — Core Mechanics Design Document

> A children's game (ages 6-12) combining real-world photography, creative drawing, and mythical crafting, set in the world of the *Classic of Mountains and Seas* (山海经).

---

## Table of Contents

1. [Photo-to-Material Conversion System](#1-photo-to-material-conversion-system)
2. [Custom Weapon Drawing & Design System](#2-custom-weapon-drawing--design-system)
3. [ML-Based Attribute Calculation System](#3-ml-based-attribute-calculation-system)
4. [Crafting / Casting Process](#4-craftingcasting-process)
5. [Educational Integration](#5-educational-integration)
6. [山海经 World Integration](#6-山海经-world-integration)

---

## 1. Photo-to-Material Conversion System

### 1.1 Overview

The child opens the in-game camera, photographs any real-world object (a leaf, a spoon, a piece of cloth, a stone, a crayon), and the game magically transforms the photograph into a **virtual crafting material** with properties loosely derived from the real object's nature.

### 1.2 Recognition Pipeline

The recognition system uses a layered approach:

```
Photo Capture
      │
      ▼
┌─────────────────────────┐
│  On-Device Preprocessing │
│  (crop, brighten, edge   │
│   detect, color extract) │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│   Object Classification  │
│   (MobileNetV4 /         │
│    CLIP-ViT distilled    │
│    for on-device use)    │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│   Material Tag Mapping   │
│   (classified object →   │
│    material category +   │
│    properties)           │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│   Mythical Material      │
│   Transformation         │
│   (real object → 山海经   │
│    fantasy material)     │
└─────────────────────────┘
```

**Key technologies:**

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| On-device classification | **MobileNetV4** or a **distilled CLIP model** (int8 quantized) | Runs offline on phones/tablets; no server latency; privacy-first (photos never leave device) |
| Fallback / edge cases | **Cloud CLIP or GPT-4V API** (opt-in, parent-gated) | For unusual objects the on-device model cannot classify |
| Material mapping | **Rule-based lookup table** + fuzzy matching | Deterministic, parent-controllable, no hallucination |

**Privacy design:** All image processing happens on-device by default. Photos are never uploaded or stored. Only the *classification result* (e.g., "leaf → plant material") is used, not the image itself.

### 1.3 The Magical Transformation

This is where the game makes the experience **fun and magical** for kids. After taking a photo:

1. **Capture Animation:** A glowing golden ring sweeps across the screen. The object shimmers with 山海经 runes.
2. **Extraction Animation:** The real object "dissolves" into particles that swirl into a miniature furnace icon.
3. **Reveal:** The particles coalesce into a **fantasy material card** with:
   - A beautiful illustrated material icon
   - The material's fantasy name (e.g., a real leaf becomes "青木灵叶" — Spirit Leaf of Azure Wood)
   - A short lore blurb connecting it to 山海经 mythology
   - Star rating for rarity and quality

**Example transformations:**

| Real Object | Fantasy Material Name | Material Category | Lore Blurb |
|-------------|----------------------|-------------------|------------|
| Green leaf | 青木灵叶 (Spirit Leaf of Azure Wood) | Plant / 木 | "Found near the Fusang Tree, said to carry the breath of spring." |
| Metal spoon | 玄铁碎片 (Fragment of Dark Iron) | Metal / 金 | "Iron from the Kunlun mines, forged by ancient earth spirits." |
| Cotton cloth | 云蚕丝缕 (Cloud-Silk Thread) | Textile / 丝 | "Woven from clouds by the Weaving Maiden of the Heavenly River." |
| Pebble/stone | 五彩灵石 (Five-Color Spirit Stone) | Stone / 土 | "A stone that absorbed the five elements over ten thousand years." |
| Seashell | 鲛人珠贝 (Merfolk Pearl Shell) | Shell / 水 | "Left behind by the merfolk of the Southern Sea." |
| Crayon/paint | 丹霞彩粉 (Crimson Elixir Powder) | Pigment / 火 | "Powdered cinnabar from the furnace of the Fire God Zhurong." |
| Rubber eraser | 灵胶软珀 (Spirit Gum Amber) | Polymer / 胶 | "Ancient tree resin hardened by magical energy." |
| Pencil/wood stick | 建木碎枝 (Jianmu Tree Splinter) | Wood / 木 | "A fragment of the World Tree that connects heaven and earth." |

### 1.4 Material Categories (五行 + Extra)

Materials are organized around an extended **五行 (Five Elements)** framework, perfect for teaching Chinese cosmology:

| Category | 五行 | Color Theme | Real-World Sources | Example Fantasy Names |
|----------|------|-------------|-------------------|----------------------|
| **Metal** | 金 | Silver/Gold | Spoons, keys, coins, foil, nails | 玄铁 (Dark Iron), 白金精 (Platinum Essence) |
| **Wood** | 木 | Green/Brown | Leaves, twigs, paper, cardboard | 青木灵叶 (Azure Leaf), 建木枝 (Jianmu Branch) |
| **Water** | 水 | Blue/Teal | Ice cubes, wet cloth, shells, water drops | 北海冰晶 (North Sea Ice Crystal), 鲛人泪 (Merfolk Tear) |
| **Fire** | 火 | Red/Orange | Matches, red objects, warm items (via color) | 祝融火种 (Zhurong's Ember), 丹霞粉 (Crimson Powder) |
| **Earth** | 土 | Brown/Yellow | Stones, soil, sand, ceramics | 息壤 (Living Soil), 五彩石 (Five-Color Stone) |
| **Silk** *(bonus)* | 丝 | White/Pink | Fabric, thread, cotton, wool | 云蚕丝 (Cloud-Silk), 天锦缎 (Heavenly Brocade) |
| **Gem** *(bonus)* | 玉 | Purple/Crystal | Glass, gems, clear plastic, beads | 和氏璧碎片 (Heshi Jade Fragment), 琉璃光 (Glazed Light) |

### 1.5 Rarity & Quality Tiers

Each material has two dimensions:

**Rarity** (how hard the object is to find / classify):

| Tier | Stars | Probability | Description |
|------|-------|-------------|-------------|
| Common | ★ | 60% | Everyday objects (leaf, paper, pebble) |
| Uncommon | ★★ | 25% | Slightly unusual objects (seashell, fabric, pencil) |
| Rare | ★★★ | 10% | Interesting objects (key, coin, feather, flower) |
| Epic | ★★★★ | 4% | Rare objects (crystal, unique natural items) |
| Legendary | ★★★★★ | 1% | Truly unique finds (identified by cloud AI as exceptional) |

**Quality** (condition of the photographed object):

| Grade | Icon | Determined By | Effect |
|-------|------|---------------|--------|
| Flawless | 完美 | Clear photo, good lighting, object fills frame | +20% stat bonus |
| Fine | 精良 | Good photo, decent lighting | +10% stat bonus |
| Normal | 普通 | Average photo quality | No bonus |
| Rough | 粗糙 | Blurry, dark, or partial photo | -5% stat penalty |

This encourages kids to **take good photos** — teaching them about lighting, focus, and composition indirectly.

### 1.6 Material Collection & Encyclopedia

Children maintain a **山海经 Material Codex** (博物志) — a collectible encyclopedia where each discovered material type is recorded with:
- Beautiful illustration
- Real-world photo thumbnail (stored locally only, in the codex)
- Mythological lore paragraph
- "Did you know?" educational fact (e.g., "Real iron is made in stars! This is why we call it 'star metal'.")

Completing the codex becomes a meta-goal that motivates exploration of the real world.

---

## 2. Custom Weapon Drawing & Design System

### 2.1 Overview

Children draw their weapon designs on a canvas. The game then **AI-beautifies** the drawing, preserving the child's creative intent while making it look polished and game-ready. The design, combined with chosen materials, determines the weapon's attributes.

### 2.2 Drawing Interface for Kids

The interface is designed for children ages 6-12 with varying motor skills:

```
┌─────────────────────────────────────────────┐
│  ┌─────────────────────────────────────┐    │
│  │                                     │    │
│  │         Drawing Canvas              │    │
│  │   (with optional guide templates)   │    │
│  │                                     │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  [✏️ Pen] [🖌️ Brush] [◻️ Shapes] [↩️ Undo] │
│  [🎨 Colors] [📐 Guides] [✨ Magic Wand]   │
│  [🗑️ Clear] [📸 Import Photo as Base]      │
│                                             │
│  ── Template Selector ──                    │
│  [Sword] [Shield] [Bow] [Staff] [Spear]    │
│  [Hammer] [Fan] [Bell] [Mirror] [Gauntlet] │
│  [Custom / Freeform]                        │
│  ────────────────────────                    │
│        [🔮 Beautify & Forge!]               │
└─────────────────────────────────────────────┘
```

**Age-adaptive modes:**

| Mode | Ages | Features |
|------|------|----------|
| **Little Smith** | 6-7 | Large brush, pre-made shapes to combine, big templates, auto-snap to grid |
| **Apprentice** | 8-9 | Freehand drawing with shape guides, more color options, symmetry tools |
| **Master Smith** | 10-12 | Full freehand, layer support, detailed templates, import photos as reference |

**Key drawing tools:**

| Tool | Description | Child-Friendly Design |
|------|-------------|----------------------|
| ✏️ Magic Pen | Main drawing tool | Stroke smoothing enabled by default; wobbly lines auto-corrected |
| 🖌️ Spirit Brush | Paint-fill tool | Like a real watercolor brush with flowing color effects |
| ◻️ Shape Stamps | Pre-made shapes (circles, triangles, stars, runes) | Drag-and-drop onto canvas; can resize and rotate |
| 📐 Guide Lines | Symmetry lines, grid, weapon outline templates | Toggle on/off; helps kids who struggle with freehand |
| ✨ Magic Wand | "Make it prettier" button — triggers AI beautification | Shows a before/after slider so kids see what changed |
| ↩️ Undo | Unlimited undo | Large, colorful button |
| 📸 Photo Base | Import a photo as a drawing base/trace guide | Connects to the material system — kids can trace objects they photographed |

### 2.3 Weapon Types (山海经 Themed)

Weapons are themed around mythical artifacts from the 山海经 universe:

| Weapon Type | 山海经 Name | Description | Real-World Inspiration |
|-------------|-------------|-------------|----------------------|
| **Sword** | 剑 (Jian) | Classic blade; balanced offense | Straight swords, daggers |
| **Shield** | 盾 (Dun) | Defensive; can reflect attacks | Shields, circular objects |
| **Bow** | 弓 (Gong) | Ranged; precision strikes | Bows, curved objects |
| **Staff** | 杖 (Zhang) | Magic-focused; elemental power | Staffs, walking sticks |
| **Spear** | 枪 (Qiang) | Long reach; piercing | Spears, poles |
| **Hammer** | 锤 (Chui) | Heavy damage; slow but powerful | Hammers, mallets |
| **Fan** | 扇 (Shan) | Wind-based; special abilities | Folding fans |
| **Bell** | 铃 (Ling) | Sound-based; area effects | Bells, chimes |
| **Mirror** | 镜 (Jing) | Reflection/illusion magic | Hand mirrors, reflective objects |
| **Gauntlet** | 拳甲 (Quanjia) | Close combat; elemental fists | Gloves, bracers |

### 2.4 AI Beautification System

The beautification system must **preserve the child's creative intent** while making the drawing look polished. Here is the approach:

#### 2.4.1 Pipeline

```
Child's Drawing
      │
      ▼
┌───────────────────────────┐
│  Stroke Analysis          │
│  (identify intended       │
│   shapes, lines, curves)  │
└────────────┬──────────────┘
             ▼
┌───────────────────────────┐
│  Intent Recognition       │
│  (what did the child      │
│   mean to draw?           │
│   skeleton → weapon type  │
│   mapping)                │
└────────────┬──────────────┘
             ▼
┌───────────────────────────┐
│  Beautification Engine    │
│  (ControlNet /            │
│   Sketch-to-Image model,  │
│   conditioned on child's  │
│   color choices & shapes) │
└────────────┬──────────────┘
             ▼
┌───────────────────────────┐
│  山海经 Styling Pass      │
│  (add mythological        │
│   decorative elements:    │
│   runes, patterns, glow)  │
└──────────────────────────┘
             ▼
┌───────────────────────────┐
│  Before / After Review    │
│  (child accepts, tweaks,  │
│   or redraws)             │
└──────────────────────────┘
```

#### 2.4.2 Technical Approach

| Component | Technology | Notes |
|-----------|-----------|-------|
| **Stroke vectorization** | Custom algorithm (Douglas-Peucker simplification + shape detection) | Runs instantly on-device; converts pixel drawing to clean vector shapes |
| **Intent recognition** | Lightweight CNN classifier trained on children's drawings of weapon shapes | Maps drawing skeleton to weapon type category; confidence threshold determines if template hint is needed |
| **Beautification** | **ControlNet** (Canny/Lineart variant) or **IP-Adapter + Stable Diffusion fine-tuned on 山海经 art style** | The child's drawing is used as a strong conditioning signal; the model generates a polished version that follows the original strokes closely |
| **Style consistency** | Fine-tuned LoRA on a curated dataset of Chinese mythological art (bronze age patterns, jade carving motifs, lacquerware designs) | Ensures all beautified weapons share a cohesive 山海经 aesthetic |
| **Parental control** | Cloud-based beautification requires opt-in; on-device fallback uses simpler rule-based vector smoothing | Privacy-first default |

#### 2.4.3 Preserving Creative Intent — Design Rules

The beautification system follows strict rules:

1. **Shape Fidelity:** If the child drew a crooked sword with a big round pommel, the beautified version is a *straighter* sword with a *big round pommel* — not a generic sword.
2. **Color Preservation:** The child's chosen colors are the primary palette. The AI adds shading and highlights but does not change base colors.
3. **Add, Don't Replace:** Decorative elements (runes, patterns, glow effects) are *added* to the design, not substituted for it.
4. **Before/After Slider:** Kids always see the before/after comparison and can accept, tweak, or reject the beautification.
5. **Iterative Refinement:** Kids can "nudge" the beautified result with additional drawing strokes, then re-beautify.

#### 2.4.4 Example Transformations

```
Child draws:              AI beautifies to:
  ╱╲                        A glowing jade sword with
 /  \                       bronze-age cloud patterns,
|    |                      the child's green and gold
|    |                      colors preserved, ancient
 \  /                       seal-script runes along
  ╲╱                        the blade, subtle particle
   |                        glow effect
  ──┴─
```

---

## 3. ML-Based Attribute Calculation System

### 3.1 Overview

This system calculates weapon stats from the **design shape**, **chosen materials**, and their **combination**. It is inspired by real-world physics and material science but abstracted into a fun, understandable system for children.

### 3.2 Calculated Attributes

| Attribute | Icon | Description | Age-Appropriate Explanation |
|-----------|------|-------------|----------------------------|
| **Attack** | ⚔️ | How much damage the weapon deals | "How hard it hits!" |
| **Defense** | 🛡️ | How well it blocks or reduces damage | "How well it protects!" |
| **Speed** | ⚡ | How fast the weapon can be swung/used | "How quick it moves!" |
| **Durability** | 💎 | How long the weapon lasts before breaking | "How tough it is!" |
| **Magic Power** | 🔮 | Elemental / special ability strength | "How much magic it channels!" |
| **Balance** | ⚖️ | How easy the weapon is to control | "How steady it feels!" |
| **Harmony** | ☯ | How well the materials work together (五行 synergy) | "How well the elements get along!" |

### 3.3 Conceptual ML Algorithm

The system is best understood as a **feature extraction → scoring pipeline** that mimics machine learning without requiring actual model inference at runtime. Think of it as a "recipe" that uses the same principles as ML (features, weights, non-linear interactions) but implemented as transparent rules.

#### 3.3.1 Feature Extraction

**From Design (Shape Analysis):**

```
Drawing Canvas
      │
      ▼
┌─────────────────────────────┐
│  Geometric Feature Extractor │
│                              │
│  • Aspect ratio (long vs     │
│    wide)                     │
│  • Symmetry score            │
│  • Total stroke length       │
│  • Enclosed area ratio       │
│  • Number of sharp points    │
│  • Curvature distribution    │
│  • Mass distribution         │
│    (pixel density map)       │
│  • Center of mass offset     │
│  • Perimeter-to-area ratio   │
└────────────┬────────────────┘
             ▼
    Shape Feature Vector:
    [0.82, 0.95, 234, 0.41, 3, 0.67, ...]
```

| Feature | Maps To | Real-World Analogy |
|---------|---------|-------------------|
| Aspect ratio (tall vs wide) | Speed vs Power | A long thin sword is fast; a wide hammer is powerful |
| Symmetry score | Balance | Symmetrical = balanced = easier to control |
| Sharp points count | Attack | More points = more piercing capability |
| Enclosed area | Defense | Larger surface area = better blocking |
| Center of mass offset | Balance | Off-center = harder to swing |
| Stroke complexity | Magic Power | Intricate designs channel more magic |

**From Materials:**

```
Selected Materials: [Material A, Material B, Material C]
      │
      ▼
┌─────────────────────────────┐
│  Material Property Lookup   │
│                              │
│  Each material has:          │
│  • Hardness (1-100)         │
│  • Flexibility (1-100)      │
│  • Density (1-100)          │
│  • Conductivity (1-100)     │
│  • 五行 element             │
│  • Quality multiplier        │
└────────────┬────────────────┘
             ▼
    Material Feature Matrix:
    [[85, 20, 90, 30, 金, 1.2],
     [30, 80, 25, 60, 木, 1.0],
     [50, 50, 50, 80, 水, 1.1]]
```

#### 3.3.2 Scoring Formula (Conceptual ML Model)

The system uses a **weighted non-linear scoring function** that mimics a neural network:

```
For each attribute A (Attack, Defense, Speed, ...):

  A = f(shape_features, material_properties, synergy)

where:

  f = σ( W_shape · shape_features
       + W_material · material_properties
       + W_synergy · synergy_bonus
       + bias )

  σ = a smooth "activation" function (sigmoid-like)
      that maps raw scores to 1-100
```

**In practice, this is implemented as:**

```python
# Pseudocode — conceptual, not implementation

def calculate_attributes(shape_features, materials):
    # Step 1: Shape-based base scores
    attack_base     = shape_features.sharp_points * 15 + shape_features.aspect_ratio * 10
    defense_base    = shape_features.enclosed_area * 20
    speed_base      = max(0, 100 - shape_features.total_stroke_length * 0.3)
    balance_base    = shape_features.symmetry_score * 80 - shape_features.center_of_mass_offset * 30
    magic_base      = shape_features.stroke_complexity * 8

    # Step 2: Material modifiers
    hardness     = avg(m.hardness for m in materials)
    flexibility  = avg(m.flexibility for m in materials)
    density      = avg(m.density for m in materials)
    conductivity = avg(m.conductivity for m in materials)

    attack_mod     = hardness * 0.6 + density * 0.4
    defense_mod    = hardness * 0.4 + flexibility * 0.3 + density * 0.3
    speed_mod      = (100 - density) * 0.5 + flexibility * 0.5
    durability_mod = hardness * 0.7 + flexibility * 0.3
    magic_mod      = conductivity * 0.8

    # Step 3: 五行 Synergy (the "magic" factor)
    elements = [m.element for m in materials]
    synergy  = calculate_wuxing_synergy(elements)  # See below

    # Step 4: Combine & normalize
    attack     = clamp(attack_base * attack_mod / 100 * (1 + synergy))
    defense    = clamp(defense_base * defense_mod / 100 * (1 + synergy))
    speed      = clamp(speed_base * speed_mod / 100 * (1 + synergy))
    durability = clamp(durability_mod * quality_multiplier)
    magic      = clamp(magic_base * magic_mod / 100 * (1 + synergy))
    balance    = clamp(balance_base)
    harmony    = clamp(synergy * 100)

    return {attack, defense, speed, durability, magic, balance, harmony}
```

#### 3.3.3 五行 Synergy System

The Five Elements have well-known generative (相生) and destructive (相克) relationships:

```
     相生 (Generative / Harmonious):
     木 → 火 → 土 → 金 → 水 → 木
     (Wood feeds Fire, Fire creates Earth/ash,
      Earth bears Metal, Metal collects Water,
      Water nourishes Wood)

     相克 (Destructive / Challenging):
     木 → 土 → 水 → 火 → 金 → 木
     (Wood parts Earth, Earth dams Water,
      Water extinguishes Fire, Fire melts Metal,
      Metal cuts Wood)
```

**Synergy scoring:**

| Combination | Relationship | Synergy Bonus |
|-------------|-------------|---------------|
| All 5 elements present | 五行俱全 (Complete Cycle) | +50% (maximum harmony) |
| 3+ elements in generative chain | 相生流转 (Flowing Generation) | +30% |
| 2 elements in generative relationship | 相生 (Generation) | +15% |
| 2 elements in destructive relationship | 相克 (Conflict) | -10% (but unlocks "chaos" special ability) |
| Same element repeated | 专精 (Specialization) | +20% to that element's attribute, -10% to others |
| All same element | 极致 (Ultimate) | +40% to one attribute, -20% to all others |

**Educational angle:** Kids learn the 五行 relationships through experimentation. They discover that combining Water + Metal materials gives a bonus (Metal generates Water), while Water + Fire gives a penalty but a unique "steam explosion" special ability.

### 3.4 Making It Feel Fair and Magical

| Design Principle | Implementation |
|-----------------|----------------|
| **Transparency** | After calculation, show a "Forge Report" card: "Your weapon got high Attack because it has 3 sharp points and uses Dark Iron (hardness: 85)!" |
| **Predictability** | Before forging, show estimated stat ranges as the child selects materials — "This combination looks like it will be strong in Attack!" |
| **Surprise bonuses** | Occasionally, rare combinations trigger "discovery" bonuses — "You found a secret combination! Ancient smiths called this the Dragon's Breath!" |
| **No "wrong" answers** | Every combination produces a valid weapon. Some are better at certain things, but no weapon is useless. A "bad" weapon might excel in an unexpected attribute. |
| **Visual feedback** | During calculation, show a miniature forge scene where the weapon's attributes manifest as colored flames (red = attack, blue = defense, etc.) |

### 3.5 Educational Integration — Teaching Through Stats

Each attribute display includes a "Learn More" button:

| Attribute | Educational Topic | Example Fact |
|-----------|------------------|--------------|
| Attack (Hardness) | Material science | "Diamond is the hardest natural material! It can scratch almost anything." |
| Defense (Area) | Geometry | "A larger shield blocks more because area = width × height!" |
| Speed (Weight/Density) | Physics | "Lighter things move faster — that's why sprinters wear light shoes!" |
| Durability (Flexibility + Hardness) | Engineering | "The best swords are hard AND slightly flexible, so they don't shatter!" |
| Magic Power (Conductivity) | Electricity / Energy | "Metals conduct electricity because their electrons can move freely!" |
| Balance (Symmetry) | Mathematics | "Symmetrical objects are easier to control — that's why most animals are symmetrical!" |
| Harmony (五行) | Chinese philosophy | "Ancient Chinese thinkers believed everything is made of five elements that interact!" |

---

## 4. Crafting / Casting Process

### 4.1 Overview

The forging process is the **climax** — the moment when design and materials come together to create the actual weapon. It is both a **mini-game** and a **visual spectacle**, designed to be exciting, participatory, and satisfying.

### 4.2 The Forge Experience — Three-Act Structure

```
Act 1: Preparation    Act 2: The Forge       Act 3: The Reveal
     (30 seconds)          (60-90 seconds)        (20 seconds)
          │                      │                      │
          ▼                      ▼                      ▼
    ┌─────────────┐       ┌──────────────┐       ┌──────────────┐
    │ Choose      │       │ Interactive   │       │ Weapon       │
    │ materials,  │  ──►  │ Forging       │  ──►  │ Emerges with │
    │ review      │       │ Mini-Game     │       │光芒 (radiant │
    │ design      │       │               │       │ light & fanfare)│
    └─────────────┘       └──────────────┘       └──────────────┘
```

### 4.3 Act 1: Preparation — The Smithy Screen

The child enters a beautifully rendered ancient Chinese smithy (锻造坊). The screen shows:

- **The Forge:** A glowing furnace in the center, animated with dancing flames
- **The Anvil:** Where the weapon will take shape
- **Material Slots:** 3-5 slots where collected materials are placed
- **Design Preview:** The child's beautified weapon drawing, displayed on a scroll

The child:
1. Places materials into slots (drag and drop)
2. Sees a live preview of estimated stats updating
3. Names their weapon (text input or voice-to-text)
4. Presses the **大铸 (Great Forge)** button

**Harmony check:** If the materials have good 五行 synergy, the forge flames glow with harmonious colors. If there's conflict, the flames flicker unpredictably — building anticipation.

### 4.4 Act 2: The Forging Mini-Game

The mini-game is **age-appropriate** and **varied** — it changes based on the weapon type and materials, keeping it fresh.

#### Mini-Game Types

| Type | Ages | Description | Controls |
|------|------|-------------|----------|
| **Rhythm Hammer** | 6-12 | Hit the anvil on the beat — timing matters! | Tap/swing when the hammer icon aligns with the target zone |
| **Temperature Control** | 8-12 | Keep the furnace at the right temperature by fanning the flames | Swipe up/down to fan; watch a temperature gauge |
| **Elemental Balancing** | 8-12 | Balance the five elements by rotating rings into alignment | Rotate concentric rings to match colored markers |
| **Quench Challenge** | 6-12 | Guide the glowing weapon into a pool of water/elemental liquid at the right moment | Drag the weapon to the target pool when the indicator turns green |
| **Rune Inscription** | 10-12 | Trace ancient runes onto the weapon | Draw along glowing guide paths |

**Rhythm Hammer (primary mini-game, all ages):**

```
    ╔═══════════════════════════════════╗
    ║     [====|====]   ← Target zone   ║
    ║         ↑                        ║
    ║    Moving cursor                 ║
    ║                                   ║
    ║       🔨  [TAP NOW!]             ║
    ║                                   ║
    ║  Combo: ★★★  Perfect: 7/10       ║
    ╚═══════════════════════════════════╝
```

- A cursor moves across a target zone
- The child taps/clicks when the cursor is in the zone
- **Perfect** hits give maximum stat boost
- **Good** hits give moderate boost
- **Miss** gives a small penalty (but never ruins the weapon)
- **Combo streaks** give bonus multipliers
- The number of hits matches the weapon's "complexity" — simple weapons need fewer hits, complex ones more

**How mini-game performance affects stats:**

```
Forge Quality Score = (perfect_hits × 3 + good_hits × 1) / total_hits

Forge Quality × Stat Multiplier:
  Perfect (90%+):  1.3×  — "传奇品质" (Legendary)
  Great (70-89%):  1.15× — "精良品质" (Fine)
  Good (50-69%):   1.0×  — "普通品质" (Standard)
  Rough (<50%):    0.9×  — "粗糙品质" (Rough)
```

This teaches kids that **practice and focus** matter — a core life lesson — while keeping the penalty gentle enough that young children don't feel discouraged.

#### Age-Adaptive Mini-Game

| Mode | Ages | Adjustments |
|------|------|-------------|
| **Little Smith** | 6-7 | Wider target zones, slower cursor, forgiving scoring, auto-complete after 3 misses |
| **Apprentice** | 8-9 | Standard zones and speed, combo bonuses |
| **Master Smith** | 10-12 | Narrower zones, faster speed, multi-stage mini-games (rhythm + temperature + quench) |

### 4.5 Act 3: The Reveal — Weapon Emerges

After the mini-game, a dramatic animation plays:

1. **The forge glows intensely** — the screen fills with light
2. **The weapon rises from the flames**, slowly rotating
3. **Ancient runes ignite** along the weapon's surface
4. **The 山海经 spirit awakens** — a mythical creature's silhouette briefly appears around the weapon
5. **The weapon card appears** with:
   - The beautified weapon illustration
   - Its name (chosen by the child)
   - All seven attributes displayed as bars/circles
   - A "power level" summary
   - Any special abilities unlocked
   - A rarity designation (based on materials + forge quality)

**Fanfare elements:**
- Satisfying sound effects (bell chime, whoosh, deep gong)
- Screen shake on reveal
- Particle effects matching the weapon's dominant element
- A short narration: "The [weapon name] has been born! Its [element] power flows through the ancient forging techniques of the Kunlun smiths..."

### 4.6 Post-Forge: Testing & Playing

After forging, the child can:

1. **Test the weapon** in a safe "training ground" — hit practice dummies, see damage numbers fly
2. **Compare** with previously forged weapons
3. **Equip** it for use in 山海经 adventure modes (exploration, creature encounters, puzzles)
4. **Share** the weapon card (screenshot or shareable link with parent permission)

---

## 5. Educational Integration

The entire game is designed as a **stealth learning** experience — children are having so much fun that they don't realize they're learning.

### 5.1 Subjects Covered

| Subject | How It's Taught |
|---------|----------------|
| **Physics** | Weight, balance, density, force through material selection and weapon design |
| **Chemistry** | Material properties, conductivity, hardness through the material system |
| **Mathematics** | Geometry (shapes, area, symmetry), ratios, percentages through stat calculations |
| **Chinese Culture** | 山海经 mythology, 五行 philosophy, ancient Chinese terminology |
| **Art & Design** | Drawing, color theory, composition through weapon design |
| **Biology / Nature** | Material sources (leaves, shells, wood) connect to natural world exploration |
| **Engineering** | Trade-offs in design (speed vs power, durability vs weight) |

### 5.2 The "Codex of Knowledge"

Every interaction unlocks entries in a collectible codex:

- **Photographing a leaf?** → Unlock entry about photosynthesis and the Fusang Tree myth
- **Using metal material?** → Unlock entry about how stars forge heavy elements
- **Creating a symmetrical weapon?** → Unlock entry about symmetry in nature and mathematics
- **Combining Fire + Water?** → Unlock entry about steam power and the Great Yu controlling the floods

### 5.3 Parent Dashboard

A parent-facing dashboard (accessible via PIN) shows:
- What materials the child has discovered
- What educational topics they've been exposed to
- How many weapons they've forged
- Suggested real-world activities ("Your child has been exploring plant materials — try a nature walk this weekend!")

---

## 6. 山海经 World Integration

### 6.1 The Setting

The game is set in a fantastical version of the 山海经 world, where:

- The **Nine Provinces** (九州) are the explorable regions
- **Mythical creatures** ( creatures from the text) are encountered as allies, puzzles, or "boss" challenges
- **Ancient smiths** serve as NPCs who teach forging techniques
- The player character is a young **apprentice smith** destined to reforge the broken artifacts of the ancient gods

### 6.2 Key Characters & Creatures

| Character | Role | 山海经 Origin |
|-----------|------|---------------|
| **Zhurong** (祝融) | Fire God; teaches fire-based forging | 山海经 · 海外南经 |
| **The Weaving Maiden** (织女) | Teaches silk/textile materials | 山海经 references |
| **Jingwei** (精卫) | A little bird who fills the sea; encourages persistence | 山海经 · 北山经 |
| **Kunlun Smiths** | Ancient master smiths who teach advanced techniques | Kunlun Mountain mythology |
| **Nine-Tailed Fox** (九尾狐) | A trickster who gives special material quests | 山海经 · 南山经 |

### 6.3 Adventure Modes

| Mode | Description | Educational Angle |
|------|-------------|-------------------|
| **Forge & Explore** | Use forged weapons to overcome obstacles in the 九州 | Problem-solving, applying knowledge |
| **Creature Encyclopedia** | Encounter and befriend 山海经 creatures by forging gifts they like | Cultural literacy, empathy |
| **Elemental Trials** | Puzzles that require understanding of 五行 relationships | Systems thinking, Chinese philosophy |
| **Smith's Challenge** | Weekly forging challenges with specific constraints | Creativity under constraints |

---

## Appendix A: Example Full Workflow

Here is how a complete game session might look:

1. **Emma (age 8)** goes to the garden and photographs a **pinecone**.
2. The game recognizes it as a natural object → transforms it into **"松果灵核" (Pinecone Spirit Core)**, a **Rare Wood-element material**.
3. Emma opens the **Drawing Studio**, selects the **Staff** template, and draws a long staff with a spiral top.
4. She hits **Beautify** — the AI transforms her drawing into a glowing staff with bark-like texture and a spiraling crystal at the top, preserving her design.
5. She places her **Pinecone Spirit Core** (Wood) and a **Dark Iron Fragment** (Metal, from a spoon photographed earlier) into the material slots.
6. The game shows estimated stats: High Magic Power (Wood + intricate design), moderate Attack (Metal), good Harmony (Metal generates Water, Wood feeds Fire — partial cycle).
7. Emma names it **"春藤杖" (Spring Vine Staff)** and presses **大铸**.
8. She plays the **Rhythm Hammer** mini-game, achieving 8/10 perfect hits.
9. The staff emerges with a Wood-element aura, stats calculated as:
   - Attack: 45
   - Defense: 30
   - Speed: 55
   - Durability: 60
   - Magic Power: **85**
   - Balance: 70
   - Harmony: 65
10. Emma tests it in the Training Ground, watching vines sprout when she swings it.
11. She unlocks a codex entry about **pinecone seed dispersal** and the **Fusang Tree** myth.

---

## Appendix B: Technical Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    Game Client                       │
│  (Unity / Godot / Flutter — cross-platform)         │
├──────────┬──────────┬──────────────┬────────────────┤
│ Camera & │ Drawing  │ Forge        │ Adventure      │
│ Material │ Studio   │ Mini-Game    │ Mode           │
│ System   │          │              │                │
├──────────┴──────────┴──────────────┴────────────────┤
│  On-Device ML: MobileNetV4 (classification)         │
│  On-Device ML: ControlNet/LoRA (beautification)     │
│  Rule Engine: Attribute calculation (transparent)   │
│  Local Storage: Materials, weapons, codex (SQLite)   │
├─────────────────────────────────────────────────────┤
│  Optional Cloud Services (parent opt-in):           │
│  • Advanced classification fallback                 │
│  • Weapon card sharing                              │
│  • Weekly challenges sync                           │
│  • Parent dashboard                                 │
└─────────────────────────────────────────────────────┘
```

---

*Document version: 1.0 | Realmforge Design Team | 2026-04-09*
