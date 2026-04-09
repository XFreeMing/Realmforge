# Realmforge (铸造世界) — Companion, Event & NPC Systems Design

> Three interconnected systems for the 山海经 children's forging/adventure game.
> Builds on: beast_and_combat_design.md, unified_economy_attributes_design.md, DESIGN_WORLD_LORE.md, technical-architecture.md

---

## Table of Contents

1. [Beast Companion & Capture System](#1-beast-companion--capture-system)
   - 1.1 Pacify vs Capture
   - 1.2 Companion Roster & Active Limits
   - 1.3 Companion Combat Mechanics
   - 1.4 Beast Sanctuary (灵兽园)
   - 1.5 Companion Bond Progression
   - 1.6 Breeding Mechanics
   - 1.7 Data Structures
2. [Event & Dynamic World System](#2-event--dynamic-world-system)
   - 2.1 Event Taxonomy & Catalog
   - 2.2 Event Trigger Logic
   - 2.3 Event Frequency & Duration
   - 2.4 What Players Do During Events
   - 2.5 Event Rewards
   - 2.6 "The Fading" (黯褪) as Gameplay
   - 2.7 Festival Event Design
   - 2.8 World Boss Encounter Flow
   - 2.9 Data Structures & Event Engine
3. [NPC Quest & Dialogue System](#3-npc-quest--dialogue-system)
   - 3.1 NPC Roster & Personalities
   - 3.2 Quest Types & Structure
   - 3.3 Quest Lifecycle (Given → Tracked → Completed)
   - 3.4 Quest Reward Structure
   - 3.5 Dialogue System Architecture
   - 3.6 Quest Journal UI
   - 3.7 NPC Quests Tied to "The Fading" Storyline
   - 3.8 Data Structures
4. [Cross-System Integration](#4-cross-system-integration)

---

## 1. Beast Companion & Capture System

### 1.1 Pacify vs Capture — Two Distinct Outcomes

The game has two ways to resolve a beast encounter non-violently: **安抚 (Pacify)** and **捕获 (Capture)** via the Net weapon. They produce different outcomes.

| Aspect | 安抚 (Pacify) | 捕获 (Capture) |
|--------|---------------|----------------|
| **Weapon used** | Drum (鼓) — rhythm mini-game | Net (网) — timing + area mini-game |
| **Mini-game** | "心灵共鸣" — match the beast's spirit rhythm | "天罗地网" — throw net at the right moment when the beast is within the target zone |
| **Success condition** | Fill the "Calm Meter" to 100% by hitting rhythm beats | Land 3 successful net throws before the beast escapes (beasts have an Escape Counter: 3-8 depending on species) |
| **Immediate outcome** | Beast is calmed, drops bonus materials (+50% drop rate), grants +2 bond XP with that species | Beast is caught in a 灵兽囊 (Spirit Pouch) and added to the player's companion roster |
| **Companion?** | No. The beast returns to the wild but remembers you. Future encounters with this species have -10% escape chance and +10% pacify success rate. | Yes. The captured beast becomes a permanent companion (if roster space is available). |
| **Bond XP earned** | +1 per pacify success (species bond) | +3 on capture + ongoing bond from usage |
| **Best for** | Players who want materials + bond progression without managing companions | Players who want active combat partners |
| **Restrictions** | Available on all beasts except World Bosses | Only works on beasts whose level is within ±5 of the player's level. Bosses and Mythic beasts cannot be captured. |

**Net weapon specifics:**

| Net Tier | Chinese | Capture Zone Size | Max Throws | Beast Level Range | Unlock Condition |
|----------|---------|-------------------|------------|-------------------|------------------|
| T1 | 藤编网 (Vine Net) | 30% of beast sprite | 3 | ±3 levels | Starting equipment from Grandma Yan |
| T2 | 灵丝网 (Spirit Silk Net) | 40% of beast sprite | 4 | ±5 levels | Crafted with 丝灵 × 3 + 木灵 × 2 |
| T3 | 天罗网 (Heaven Net) | 55% of beast sprite | 5 | ±7 levels | Crafted with 玉灵 × 2 + 丝灵 × 3 + 金灵 × 1 |
| T4 | 缚灵网 (Spirit Bind Net) | 70% of beast sprite | 6 | ±10 levels | Reward from restoring a full realm fragment |

### 1.2 Companion Roster & Active Limits

**Two-tier companion storage:**

```
┌───────────────────────────────────────────────┐
│                Companion System               │
│                                               │
│  ┌─────────────────────┐  ┌────────────────┐  │
│  │  随行队列            │  │  灵兽园         │  │
│  │  (Active Roster)     │  │  (Sanctuary)   │  │
│  │                     │  │                │  │
│  │  Max 3 beasts       │  │  Max 12 beasts │  │
│  │  fight alongside    │  │  stored, can   │  │
│  │  the player         │  │  be swapped in │  │
│  └─────────────────────┘  └────────────────┘  │
└───────────────────────────────────────────────┘
```

**Active Roster rules:**

| Rule | Detail |
|------|--------|
| **Active slots** | 3 beasts max. Displayed on-screen as spirit orbs following the player. |
| **Age-adaptive limits** | Ages 6-7: 1 active slot (simpler management). Ages 8-9: 2 slots. Ages 10-12: 3 slots. |
| **Element diversity bonus** | If all 3 active beasts have different elements: +10% to all attributes in combat. |
| **Element stacking bonus** | If all 3 active beasts share the same element: +25% to that element's damage, -10% to others. |
| **Swapping** | Can only swap at a 灵兽园 or at a 祭灵台 (Spirit Altar) found in world locations. Cannot swap during combat. |
| **Recall** | Player can dismiss a beast mid-combat (it retreats to spirit form, no penalty). Cooldown: 3 combat rounds before it can be summoned again. |

### 1.3 Companion Combat Mechanics

Companions fight **alongside** the player in an **auto-assist** system. The child does not directly control companion actions — companions act intelligently based on their bond level and personality.

**Companion action flow per combat round:**

```
Round Start
     │
     ├── Player Turn (child chooses action + mini-game)
     │
     ├── Companion Phase (auto-resolved)
     │     │
     │     ├── Check companion AI behavior tree
     │     │     ├── If beast HP < 30%: try to finish
     │     │     ├── If player HP < 30%: try to protect/heal
     │     │     ├── If beast has elemental weakness: exploit it
     │     │     └── Otherwise: standard attack
     │     │
     │     ├── Resolve companion attack (no mini-game for child)
     │     │     Damage = Companion_Attack × (1 + Bond_Level × 0.05)
     │     │
     │     └── Check for companion special ability trigger
     │           (based on bond level, see 1.5)
     │
     └── Beast Turn
```

**Companion damage formula:**

```
Companion_Damage = Base_Attack × Level_Scale × Bond_Multiplier × Element_Multiplier

Where:
  Base_Attack    = Beast template base attack (from species data)
  Level_Scale    = 1.0 + (Companion_Level - 1) × 0.08
  Bond_Multiplier = 1.0 + Bond_Level × 0.05
    (Bond Level 0-10, so 1.0x to 1.5x)
  Element_Multiplier =
    2.0 if exploiting beast weakness (五行相克)
    1.0 if neutral
    0.5 if resisted (五行相生 in reverse)
```

**Companion abilities by bond level:**

| Bond Level | Unlocks | Effect |
|------------|---------|--------|
| 0 (初识) | Basic attack only | Companion deals 50% of its base attack |
| 1 (熟悉) | Standard attack | Companion deals 75% base attack, uses elemental attacks |
| 2 (信任) | Defensive assist | If player is hit while companion is active, 20% chance companion intercepts (blocks 40% of damage) |
| 3 (共鸣) | Special ability | Companion uses its unique species ability once per combat (e.g., Nine-Tailed Fox: illusion that stuns beast for 1 round) |
| 4 (共生) | Combo attack | Once per combat, companion and player can perform a combo: child's attack + companion's attack merge into a single powerful strike (150% combined damage) |

**Companion death & injury:** Companions never "die." If a companion's HP reaches 0, it enters **灵憩 (Spirit Rest)** for 10 minutes of real time. During Spirit Rest, it cannot be used but slowly regenerates. The child can speed recovery by feeding it its preferred material type (instant recover).

### 1.4 Beast Sanctuary (灵兽园)

The 灵兽园 is a dedicated location where the player stores, manages, and breeds companions.

**Unlock requirement:** Complete the quest "小澜的请求" from Little Lan in Act 2. The player must have captured at least 2 beasts and restored 1 faded fragment.

**Space limits:**

| Upgrade | Capacity | Cost (灵魄) | Material Cost | Unlock |
|---------|----------|-------------|---------------|--------|
| Starting | 4 slots | — | — | Quest reward |
| Expansion 1 | 6 slots | 200 | 木灵 × 5, 土灵 × 3 | Player level 5 |
| Expansion 2 | 8 slots | 400 | 木灵 × 8, 水灵 × 5, 生灵 × 2 | Player level 8 |
| Expansion 3 | 10 slots | 600 | 木灵 × 10, 玉灵 × 3, 生灵 × 3 | Player level 12 |
| Expansion 4 | 12 slots | 1000 | 木灵 × 15, 丝灵 × 5, 生灵 × 5 | Complete "灵兽园大师" quest chain |

**Sanctuary features:**

| Feature | Description |
|---------|-------------|
| **Beast Pens** | Each occupied slot shows the beast's animated sprite, level, bond level, and mood. Beasts have idle animations (playing, sleeping, eating). |
| **Feeding Station** | Feed beasts materials to gain bond XP and beast XP. Each beast has 2 preferred essence types (gives 2x bond XP) and 1 disliked type (gives 0.5x). |
| **Breeding Ground (配对池)** | Place two compatible beasts here to attempt breeding (see 1.6). |
| **Training Dummy** | Practice combat with sanctuary beasts without risk. Unlocks at sanctuary level 2. |
| **Bond Shrine** | View bond progress for all beast species encountered. Milestone rewards at each species bond level 3 and 5. |

**Beast mood system:** Each beast in the sanctuary has a mood that changes based on recent activity.

| Mood | Chinese | Trigger | Effect |
|------|---------|---------|--------|
| Happy | 开心 | Used in combat recently, fed preferred food | +10% bond XP gain, more likely to trigger special abilities |
| Restless | 躁动 | Not used in combat for 3+ days | -5% bond XP gain, may refuse feeding once |
| Lonely | 孤单 | No other beasts in sanctuary for 2+ days | Slight XP penalty, visual cue (sitting alone) |
| Bonded | 亲密 | Placed near a compatible beast in sanctuary | +15% bond XP gain for both, unlocks breeding compatibility earlier |
| Excited | 兴奋 | During a world event | Double XP from next feeding, may trigger spontaneous mutation (1% chance) |

### 1.5 Companion Bond Progression

Bond is tracked **per individual companion**, not per species. Each companion has its own bond level (0-10).

**Bond XP sources:**

| Source | Bond XP | Frequency |
|--------|---------|-----------|
| Active in combat (round survived) | +1 | Per round |
| Landing a hit | +2 | Per hit |
| Using special ability successfully | +5 | Per use |
| Feeding preferred material at sanctuary | +3 | Per feeding |
| Feeding non-preferred material | +1 | Per feeding |
| Completing a beast-specific NPC quest | +10 | One-time |
| Pacifying the same species | +1 (species bond) | Per pacify |
| Participating in world event | +5 | Per event |

**Bond level thresholds:**

| Bond Level | Name (Chinese) | Name (English) | Total Bond XP Required | Unlocks |
|------------|----------------|----------------|----------------------|---------|
| 0 | 初识 | Acquainted | 0 | Basic assist (50% damage) |
| 1 | 熟悉 | Familiar | 20 | Full elemental attacks (75% damage) |
| 2 | 信任 | Trusted | 60 | Defensive intercept (20% chance, 40% block) |
| 3 | 共鸣 | Resonant | 120 | Unique species ability (1x per combat) |
| 4 | 默契 | Synced | 200 | Combo attack (150% combined damage, 1x per combat) |
| 5 | 知心 | Kindred | 320 | Companion auto-heals 5% HP per round |
| 6 | 同心 | United | 480 | Companion gains +1 mutation slot |
| 7 | 灵犀 | Telepathic | 700 | Companion can act twice per round (10% chance) |
| 8 | 化形 | Shape-Shift | 1000 | Companion transforms visually, gains ultimate ability |
| 9 | 归真 | True Form | 1500 | Ultimate ability damage +50%, no Spirit Rest needed |
| 10 | 永恒 | Eternal | 2200 | Permanent passive: +5% to all player stats while companion is active |

**Visual bond indicators:**

| Bond Level | Visual Effect |
|------------|---------------|
| 0-1 | Beast appears normal |
| 2-3 | Soft glow aura matching beast's element |
| 4-5 | Spirit trail follows beast; occasional heart particles |
| 6-7 | Beast's eyes glow; constellation pattern appears on its body |
| 8-9 | Beast is surrounded by a visible spirit link to the player character |
| 10 | Beast has a unique "Eternal" form — full visual redesign with enhanced effects |

### 1.6 Breeding Mechanics

**Breeding prerequisites:**

| Requirement | Detail |
|-------------|--------|
| Both beasts must be in the sanctuary | Cannot breed active roster beasts |
| Minimum bond level | Both beasts must be at bond level 2+ |
| Compatibility check | Beasts must not be the same individual (obvious), and must not share a parent within 2 generations (inbreeding penalty) |
| Breeding cost | 50 灵魄 + 2 T2 materials matching at least one beast's element |
| Cooldown | After breeding, both parents have a 24-hour cooldown before they can breed again |

**Breeding process:**

```
1. Player places two compatible beasts in the Breeding Ground
2. A "bonding" mini-game plays (drag spirit threads between the two beasts)
   - Successful thread connections increase offspring quality
   - Minimum 3 connections required to produce an egg
   - Maximum 7 connections (perfect breeding)
3. An 灵兽蛋 (Spirit Egg) appears
4. Egg incubation takes 10-30 minutes (real time) based on parent rarity
   - Player can speed up by tapping/rubbing the egg (mini-game)
   - Each successful rub reduces time by 1 minute
5. Egg hatches → new beast with inherited + mutated genes
```

**Inheritance rules:**

| Gene Segment | Inheritance Rule |
|-------------|-----------------|
| Species | 50% chance from Parent A, 50% from Parent B (if different species; if same species, offspring is same species) |
| Appearance genes | 50% from each parent (random crossover per gene) |
| Ability genes | 1 random ability from each parent, plus 10% chance of a new spontaneous ability |
| Element | Determined by species. If hybrid species, element = most common parent element |
| Stats | Average of parents' stats at same level, then ±15% random variation |
| Mutation rarity | Inherit parents' mutations. 5% chance per mutation of upgrading one tier (N→R, R→SR, etc.) |
| Spontaneous mutation | 10% base chance. +5% if both parents are SR+. +10% during a world event. |

**Inbreeding penalty:** If parents share a grandparent, offspring stats are reduced by 20% and spontaneous mutation chance drops to 2%. The game warns the player: "These two seem too closely related..."

### 1.7 Data Structures

```yaml
Companion:
  beast_id: UUID                    # links to the Beast template
  owner_id: UUID
  instance_id: UUID                 # unique instance (from mutation system)
  nickname: string                  # player-assigned name
  level: int                        # 1-50
  experience: int
  hp: int                           # current HP
  max_hp: int
  bond_level: int                   # 0-10
  bond_xp: int                      # total accumulated
  mood: enum [happy, restless, lonely, bonded, excited]
  last_used_in_combat: timestamp
  last_fed: timestamp
  preferred_elements: [essence_type, essence_type]
  disliked_elements: [essence_type]
  is_active: bool                   # in active roster?
  active_slot: int                  # 0-2, null if not active
  spirit_rest_until: timestamp      # null if not resting
  gene_encoding: JSONB              # inherited from beast system

CompanionBondMilestone:
  species_id: UUID
  bond_level: int                   # 3 or 5 (milestone levels)
  reward_claimed: bool
  reward_type: enum [material, recipe, sanctuary_upgrade]
  reward_id: UUID

BreedingPair:
  parent_a_id: UUID
  parent_b_id: UUID
  placed_at: timestamp
  connection_count: int             # 0-7 from mini-game
  egg_created: bool
  egg_hatch_time: timestamp
  offspring_id: UUID                # set on hatch
```

---

## 2. Event & Dynamic World System

### 2.1 Event Taxonomy & Catalog

Events are organized into four tiers:

| Tier | Name | Frequency | Duration | Player Impact |
|------|------|-----------|----------|---------------|
| **T1** | 微象 (Minor Phenomena) | Every 2-4 hours | 15-30 minutes | Local area effect, bonus materials |
| **T2** | 异象 (Notable Events) | Every 1-2 days | 1-3 hours | Multi-area effect, special encounters |
| **T3** | 盛典 (Festivals) | Real-world calendar (see 2.7) | 3-7 days | Global event, exclusive rewards |
| **T4** | 劫变 (Cataclysms) | Story-gated or rare random | 30-60 minutes | World boss, Fading acceleration, major rewards |

**Complete event catalog:**

| Event | Tier | Chinese | Trigger | Areas Affected | Description |
|-------|------|---------|---------|----------------|-------------|
| Meteor Shower | T1 | 星雨 | Time-based (night, random) | Cloud Realm, Mountain Realm peak areas | Falling star fragments spawn T2-T3 火灵/玉灵 materials |
| Coral Bloom | T1 | 珊瑚绽 | Time-based (spring, full moon) | Sea Realm | Coral releases spore particles; collect 丝灵 and 水灵 materials |
| Tree Migration | T2 | 树迁 | Player activity (restored 3+ fragments in Forest Realm) | Forest Realm | Trees physically relocate, revealing hidden paths and chests |
| Cloud Storm | T1 | 云暴 | Random (cloudy weather in-game) | Cloud Realm | Lightning strikes create temporary 雷池 pools with T3 materials |
| Spirit Tide | T2 | 灵潮 | Fading meter drops below 40% | All realms | Beasts become more active; double bond XP for 1 hour |
| Dream Echo | T1 | 梦回 | Night time in Dream Realm | Dream Realm | Past player actions replay as ghost images; follow them to find lost items |
| Aurora Veil | T2 | 极光幕 | Random (after Cloud Storm + Meteor Shower within 24h) | Cloud + Dream Realm boundary | Rare 玉灵 materials, unique beast spawns |
| Realm Quake | T4 | 境震 | Fading meter drops below 20% | Random realm | World boss spawns; realm loses 5% vitality if not defeated |
| Nian Beast Arrival | T3 | 年兽来 | Spring Festival (real calendar) | All realms | Special festival boss (see 2.7) |
| Dragon Boat Race | T3 | 龙舟赛 | Dragon Boat Festival | Sea Realm | Racing mini-game with rewards |
| Moonlit Gathering | T3 | 月聚 | Mid-Autumn Festival | Dream Realm | Cooperative puzzle event |
| The Fading Surge | T4 | 黯褪涌 | Inactivity (7+ days no login) or story trigger | All realms | Global meter drops, grey areas expand, beasts become aggressive |

### 2.2 Event Trigger Logic

Events use a **hybrid trigger system** with three trigger types:

```
┌─────────────────────────────────────────────────────────────┐
│                    Event Trigger Engine                      │
│                                                              │
│  Three trigger channels (evaluated every game tick):         │
│                                                              │
│  1. TIME-BASED TRIGGERS (60% of events)                     │
│     ├── Game clock checks (hour, day, season, moon phase)   │
│     ├── Real-world calendar checks (festivals)              │
│     └── Cooldown timers (minimum time between same event)   │
│                                                              │
│  2. ACTIVITY-BASED TRIGGERS (25% of events)                 │
│     ├── Player milestones (restored N fragments,             │
│     │   reached level X, captured Y beasts)                 │
│     ├── World state thresholds (Fading meter < X%)          │
│     └── Chain triggers (Event A completed → Event B eligible)│
│                                                              │
│  3. RANDOM TRIGGERS (15% of events)                         │
│     ├── Weighted random roll each game hour                 │
│     ├── Weight adjusted by: player level, recent events,    │
│     │   current realm, Fading meter                         │
│     └── Pity system: if no T2+ event in 48h, weight ×2      │
└─────────────────────────────────────────────────────────────┘
```

**Time-based trigger evaluation (every game hour):**

```python
def evaluate_time_triggers(game_time, player_state):
    candidates = []

    # Meteor shower: night hours (20:00-04:00), 15% base chance
    if game_time.hour >= 20 or game_time.hour <= 4:
        if game_time.hour % 2 == 0:  # check every 2 hours
            candidates.append(Event.METEOR_SHOWER)

    # Coral bloom: spring season, full moon, 25% chance
    if game_time.season == "spring" and game_time.moon_phase == "full":
        candidates.append(Event.CORAL_BLOOM)

    # Cloud storm: any time, 10% base chance
    if game_time.hour % 3 == 0:
        candidates.append(Event.CLOUD_STORM)

    # Filter by cooldown (same event cannot trigger within N hours)
    candidates = [e for e in candidates
                  if game_time.hours_since(e.last_trigger) >= e.cooldown_hours]

    # Roll for each candidate
    triggered = []
    for event in candidates:
        weight = event.base_chance
        weight *= _fading_modifier(player_state.fading_meter)
        weight *= _level_modifier(player_state.level)
        if random.random() < weight:
            triggered.append(event)

    return triggered
```

**Cooldown enforcement:**

| Event | Minimum Cooldown |
|-------|-----------------|
| Meteor Shower | 4 hours |
| Coral Bloom | 24 hours |
| Tree Migration | 72 hours |
| Cloud Storm | 6 hours |
| Spirit Tide | 48 hours |
| Dream Echo | 12 hours |
| Aurora Veil | 72 hours |
| Realm Quake | 168 hours (1 week) |

### 2.3 Event Frequency & Duration

**Expected event load per day (average):**

| Tier | Events Per Day | Duration | Overlap |
|------|---------------|----------|---------|
| T1 (Minor) | 2-4 | 15-30 min | Can overlap with each other |
| T2 (Notable) | 0.5-1 | 1-3 hours | Cannot overlap with other T2+ events |
| T3 (Festival) | 0 (periodic) | 3-7 days | Overrides all other events |
| T4 (Cataclysm) | 0.05-0.1 | 30-60 min | Forces all T1/T2 events to pause |

**Event pacing rules:**

1. At most one T2 event active at a time.
2. At most two T1 events active simultaneously.
3. T3 festivals suppress all T1/T2 events in affected realms (festival activities take priority).
4. T4 cataclysms force-pause all other events and notify the player immediately.
5. **Pity system:** If no T2+ event has occurred in 48 real hours, the next time-based trigger roll has doubled weight.

### 2.4 What Players Actually Do During Events

**Meteor Shower (星雨):**
- Player climbs to a high vantage point (Mountain peak, Cloud floating island)
- **Mini-game:** "星轨采集" — falling stars trace paths across the screen; player drags a collection net along the path
- Each collected star fragment yields 1-3 T2 火灵/玉灵 materials
- Collecting 10+ fragments in one shower unlocks a "Starfall Recipe"

**Coral Bloom (珊瑚绽):**
- Player swims through blooming coral formations
- **Mini-game:** "花蕊寻珠" — coral flowers open and close in patterns; player must enter the open flowers in the correct sequence (memory game)
- Each successful sequence yields 丝灵 and 水灵 materials
- Finding all coral sequences in one bloom unlocks a Yuan tribe exclusive recipe

**Tree Migration (树迁):**
- Player observes trees uprooting and walking to new positions
- **Activity:** "路径预测" — player places markers to predict where a specific tree will go; correct predictions reward exploration chests at the destination
- New paths reveal previously inaccessible areas for 24 hours
- Trees may leave behind "root caches" — material chests

**Cloud Storm (云暴):**
- Player navigates floating platforms while lightning strikes
- **Mini-game:** "引雷入器" — player positions a lightning rod to channel strikes into empty energy cells
- Each filled cell becomes a T3 elemental crystal
- Too many misses = temporary platform destruction (respawns after storm)

**Spirit Tide (灵潮):**
- Passive buff event: all bond XP doubled, beasts are 2x more likely to appear
- **Activity:** "灵韵共鸣" — rhythm mini-game at spirit altars; successful play grants bonus 灵魄
- Best time to capture new companions

**Dream Echo (梦回):**
- Ghost images of the player's past actions appear in the Dream Realm
- **Activity:** Follow the ghost to the location where a past action occurred; dig to find a "memory cache" containing lost items or bonus materials
- Each echo has a short puzzle (match the original action) to unlock the cache

**Aurora Veil (极光幕):**
- A shimmering curtain of light appears between Cloud and Dream realms
- **Activity:** Walk through the aurora to enter a special "Aurora Zone" with unique puzzles and rare beast encounters
- The aurora slowly fades; player must complete activities before it disappears

### 2.5 Event Rewards

| Event | Primary Rewards | Bonus Rewards (perfect performance) |
|-------|----------------|-------------------------------------|
| Meteor Shower | T2 火灵 × 3-8, T2 玉灵 × 1-3 | Starfall Recipe (T3 weapon) |
| Coral Bloom | T2 丝灵 × 3-6, T2 水灵 × 2-5 | Yuan Tribe Coral Pattern (cosmetic) |
| Tree Migration | T2-T3 木灵 × 5-10, root cache materials | New permanent path unlock |
| Cloud Storm | T3 elemental crystal × 1-3 | Lightning-inscribed weapon template |
| Spirit Tide | 2x bond XP, 2x beast spawn rate | Rare beast spawn (5% chance) |
| Dream Echo | Memory cache (random lost items × 1-3) | Echo Fragment (story lore item) |
| Aurora Veil | T3-T4 玉灵 × 1-2, unique beast encounter | Aurora Essence (permanent +1 Spirit to one weapon) |

**Participation rewards (minimum engagement):** Every event gives at least some reward even if the player does minimal interaction. This ensures children are never punished for not being "good enough."

| Engagement Level | Reward |
|-----------------|--------|
| Just showed up (event detected) | T1 material × 1 |
| Completed 1+ mini-game round | T2 material × 1-2 |
| Completed all challenges | Primary rewards + bonus |
| Perfect run (no misses) | Primary + bonus + rare recipe/recipe fragment |

### 2.6 "The Fading" (黯褪) as Gameplay

**The Fading is a global world meter** from 0-100 representing the world's vitality. It is the central mechanic tying all systems together.

**How it manifests:**

```
┌─────────────────────────────────────────────────────────────┐
│              The Fading (黯褪) Meter                        │
│                                                              │
│  100% ─────────────────────────────────────────── 0%        │
│  │  Vibrant  │  Warning  │  Danger  │  Critical │  Grey    ││
│  │  100-70%  │  70-50%   │  50-30%  │  30-10%  │  0-10%   ││
│                                                              │
│  Visual changes per stage:                                   │
│  100-70%: World is fully colored, creatures active           │
│  70-50%:  Edge areas show slight desaturation; some NPCs     │
│           mention "feeling tired"                            │
│  50-30%:  Outer realm zones become grey; fewer beast spawns; │
│           some paths blocked by grey mist; NPCs look worried  │
│  30-10%:  Major areas desaturate; beast spawn rate -50%;     │
│           Spirit Tide events become more frequent;           │
│           Realm Quake events possible                        │
│  0-10%:   Game enters "crisis mode" — most areas grey,       │
│           companion bond XP -50%, NPCs urge the player       │
│           to act; only essential areas remain vibrant         │
└─────────────────────────────────────────────────────────────┘
```

**What decreases The Fading meter:**

| Action | Fading Impact |
|--------|---------------|
| Player inactive for 3+ days | -1% per day |
| Player inactive for 7+ days | -2% per day (compounding) |
| Realm Quake event unresolved | -5% per unresolved quake |
| Completing a "dark" quest choice (rare, story-dependent) | -2% |

**What increases The Fading meter:**

| Action | Fading Impact |
|--------|---------------|
| Restore a faded realm fragment | +3-5% (depending on fragment size) |
| Complete a main storyline quest | +2-4% |
| Complete an NPC quest chain | +1-2% |
| Pacify a beast (any species) | +0.1% |
| Craft a new weapon type (first time) | +1% |
| Participate in a festival | +2% |
| Breed a new beast | +0.5% |
| Discover a new realm area | +2% |
| Photo-capture a new material type | +0.2% |

**The Fading meter is persistent** — it does not reset between sessions. It tracks the cumulative state of the world across all play sessions. The meter is displayed as a **vitality bar** on the world map screen and as a subtle **screen-edge vignette** during gameplay (more grey at edges = lower vitality).

**Anti-frustration design:** The Fading meter cannot drop below 20% through inactivity alone (it floors at 20%). This ensures that a returning child always has a playable world. The "crisis mode" (0-10%) is only reachable through story events, never through neglect.

### 2.7 Festival Event Design

Three major festivals tied to the real-world Chinese calendar. Each has unique mechanics, rewards, and narrative significance.

#### Spring Festival (春节) — 年兽 Event

**Timing:** 14 days before to 7 days after Chinese New Year (real calendar)

**Narrative:** The 年兽 (Nian Beast) — a creature afraid of red, fire, and loud noises — is terrorizing the village. The player must prepare defenses.

**Phases:**

| Phase | Duration | Activities |
|-------|----------|------------|
| **Preparation** | Days 1-7 | Craft red decorations (red 火灵 weapons deal +50% to Nian), collect 爆竹 (firecracker) materials, learn "drum rhythm" from Grandma Yan |
| **Arrival** | Day 8 | Nian Beast appears at the village edge. First encounter is scripted — it destroys a faded fragment. |
| **Confrontation** | Days 9-14 | Multi-phase boss fight (see 2.8). Each day the Nian Beast returns stronger but the player has learned new tactics. |

**Nian Beast combat mechanics:**

| Phase | Nian HP | Player Strategy |
|-------|---------|----------------|
| 1 — Fear of Red | 300 | Equip red/fire weapons. Red items deal 200% damage. |
| 2 — Fear of Noise | 500 | Use Drum weapon type. Rhythm hits deal triple damage. |
| 3 — Fear of Fire | 800 | Combine red + fire + drum for maximum damage. Companions with 火 element get +50% attack. |

**Festival rewards:**

| Reward | Type | How to Earn |
|--------|------|-------------|
| 年兽角 (Nian Horn) | T4 material | Defeat Nian Beast on Day 14 |
| 春联符 (Couple Charm) | Cosmetic | Complete all 7 preparation days |
| 红包灵 (Lucky Red Spirit) | Consumable | Daily participation (grants 2x materials for 1 hour) |
| "年兽克星" Title | Title | Defeat Nian Beast with perfect Phase 3 |

#### Dragon Boat Festival (端午) — 龙舟 Race

**Timing:** 7 days centered on the 5th day of the 5th lunar month

**Narrative:** The Sea Realm's rivers have become treacherous. The player must join the dragon boat race to deliver 粽子 (zongzi) offerings to the river spirit.

**Mechanics:**

| Activity | Description |
|----------|-------------|
| **Boat Crafting** | Player designs and forges a mini dragon boat. Boat stats (speed, stability) affect race performance. |
| **Racing** | Rhythm-based mini-game: paddle on beat, dodge obstacles (whirlpools, water spirits), collect 水灵 tokens on the course. |
| **Zongzi Delivery** | After winning races, deliver zongzi to the river spirit. This is a navigation puzzle through a maze of currents. |

**Rewards:**

| Reward | Type | How to Earn |
|--------|------|-------------|
| 龙舟鳞 (Dragon Boat Scale) | T3 material | Win 3+ races |
| 粽子灵 (Zongzi Spirit) | T2 companion (food-type beast) | Deliver zongzi to river spirit |
| 艾草符 (Mugwort Charm) | Consumable | Participate in 1 race (grants +10% water element resistance for 24h) |

#### Mid-Autumn Festival (中秋) — 月聚 (Moonlit Gathering)

**Timing:** 7 days centered on the 15th day of the 8th lunar month

**Narrative:** The 月兔 (Moon Rabbit) has scattered mooncakes across the Dream Realm. The player must collect them all before the moon wanes.

**Mechanics:**

| Activity | Description |
|----------|-------------|
| **Mooncake Hunt** | Hidden object mini-game in the Dream Realm. Mooncakes are hidden behind illusion puzzles. |
| **Lantern Lighting** | Place lanterns at specific locations to create a "moon path." Lantern placement is a spatial puzzle. |
| **Moon Rabbit Encounter** | After collecting 7 mooncakes, the Moon Rabbit appears. It asks riddles (age-adaptive difficulty). Answering correctly grants the Moon Rabbit as a temporary companion. |

**Rewards:**

| Reward | Type | How to Earn |
|--------|------|-------------|
| 月光玉 (Moonlight Jade) | T3 material | Collect all 7 mooncakes |
| 桂花酿 (Osmanthus Brew) | Consumable | Complete lantern lighting puzzle (grants +20% Spirit for 1 forge session) |
| 月兔 (Moon Rabbit) | Temporary companion | Answer 3+ riddles correctly (companion lasts 7 days) |

### 2.8 World Boss Encounter Flow

World bosses are T4 events that follow a structured encounter flow.

**Boss encounter stages:**

```
Stage 1: Omen (5-10 min before boss arrives)
     │
     ├── Visual cues: sky darkens, beasts flee, ground trembles
     ├── Audio: ominous music, distant roars
     ├── NPC warnings: nearby NPCs urge the player to prepare
     └── Player prep window: heal, equip, summon companions

Stage 2: Arrival (boss appears)
     │
     ├── Boss emerges from a tear in the realm
     ├── Boss introduction card (name, title, threat level)
     └── Combat begins

Stage 3: Multi-Phase Combat
     │
     ├── Phase 1: Boss at 100-66% HP
     │     ├── Standard attack patterns
     │     ├── Teaches the boss's weakness (visual telegraphing)
     │     └── Player learns the pattern
     │
     ├── Phase 2: Boss at 66-33% HP
     │     ├── New attack patterns added
     │     ├── Environment changes (platforms crumble, hazards appear)
     │     └── Companion special abilities become more important
     │
     └── Phase 3: Boss at 33-0% HP
           ├── Desperation mode: rapid attacks, area effects
           ├── "Final stand" mechanic: player gets one free heal
           └── Dramatic finish animation

Stage 4: Resolution
     │
     ├── Boss is pacified (never killed)
     ├── Boss leaves a gift (T4-T5 materials)
     ├── Fading meter increases +3%
     ├── World state updates (grey areas restore)
     └── NPCs celebrate and share lore
```

**Active world bosses:**

| Boss | Chinese | Realm | Difficulty | Phases | Special Mechanic |
|------|---------|-------|------------|--------|-----------------|
| 相柳 (Xiangliu) | Nine-Headed Serpent | Sea Realm | ★★★★ | 3 | Each head has a different element; must exploit the weakest head |
| 饕餮 (Taotie) | Gluttonous Beast | Mountain Realm | ★★★★★ | 4 | Absorbs materials from the environment; player must deny it resources |
| 烛龙 (Torch Dragon) | Torch Dragon | Cloud Realm | ★★★★★ | 3 | Controls day/night cycle during combat; attacks change based on light |
| 年兽 (Nian Beast) | Year Beast | All Realms | ★★★ (scales) | 3 | Weak to red/fire/noise; festival-specific |

**Boss rewards scale with performance:**

| Performance | Rewards |
|-------------|---------|
| Defeated (barely) | T4 material × 1, Fading +3% |
| Good (no companion lost to Spirit Rest) | T4 material × 2, T3 material × 3, Fading +4% |
| Excellent (no HP lost below 50%) | T4 material × 3, T5 material × 1, unique recipe, Fading +5% |
| Perfect (no damage taken) | T5 material × 2, boss companion fragment (can summon a weakened version), Fading +5%, title |

### 2.9 Data Structures & Event Engine

```yaml
WorldEvent:
  event_id: UUID
  event_type: enum [meteor_shower, coral_bloom, tree_migration, cloud_storm,
                    spirit_tide, dream_echo, aurora_veil, realm_quake,
                    spring_festival, dragon_boat, mid_autumn, nian_beast,
                    fading_surge]
  tier: enum [T1, T2, T3, T4]
  status: enum [pending, active, completed, expired]
  triggered_at: timestamp
  expires_at: timestamp
  affected_realms: [realm_id]
  affected_areas: [area_id]       # specific zones within realms
  trigger_type: enum [time, activity, random, story]
  trigger_data: JSONB             # context about what triggered it
  player_participation: JSONB
    first_seen: timestamp
    mini_games_completed: int
    rewards_claimed: [reward_id]
    performance_score: int        # 0-100
  rewards_distributed: bool

FadingState:
  current_value: int              # 0-100
  last_updated: timestamp
  history: [                      # last 30 entries for trend display
    { value: int, timestamp: timestamp, cause: string }
  ]
  crisis_mode: bool               # true if < 10%
  floor_value: int                # minimum value (20 for inactivity floor)

FestivalConfig:
  festival_type: enum [spring, dragon_boat, mid_autumn]
  real_world_start: date
  real_world_end: date
  in_game_start_offset: int       # days before real date
  in_game_end_offset: int         # days after real date
  phases: [FestivalPhase]
  rewards: [FestivalReward]

FestivalPhase:
  name: string
  day_start: int
  day_end: int
  activities: [ActivityDef]
  unlocks: [unlock_id]

EventEngine:
  # Evaluated every game hour (configurable)
  tick_interval_minutes: 60
  last_tick: timestamp

  # Cooldown tracking
  cooldowns:
    meteor_shower: int            # hours remaining
    coral_bloom: int
    tree_migration: int
    # ... etc

  # Pity system
  hours_since_last_T2_plus: int
  pity_multiplier: float          # starts at 1.0, increases over time
```

**Event engine pseudo-code:**

```python
def event_engine_tick(game_state):
    now = game_state.clock

    # 1. Check real-world calendar for festivals
    festivals = check_calendar_festivals(now.real_date)
    for fest in festivals:
        if not is_event_active(fest.event_id):
            start_event(fest)

    # 2. Check activity-based triggers
    activity_events = evaluate_activity_triggers(game_state)
    for event in activity_events:
        if cooldown_expired(event) and not is_event_active(event.id):
            start_event(event)

    # 3. Time-based random triggers
    if now.hour % game_state.tick_interval_minutes == 0:
        time_events = evaluate_time_triggers(now, game_state.player)

        # Apply pity system
        if game_state.hours_since_last_T2_plus >= 48:
            for e in time_events:
                if e.tier >= T2:
                    e.weight *= game_state.pity_multiplier

        for event in time_events:
            if random.random() < event.weight:
                if cooldown_expired(event):
                    start_event(event)
                    game_state.hours_since_last_T2_plus = 0
                    game_state.pity_multiplier = 1.0

    # 4. Update active events
    for event in active_events:
        if now >= event.expires_at:
            expire_event(event)
        else:
            update_event(event)

    # 5. Update Fading meter
    update_fading_meter(game_state)
```

---

## 3. NPC Quest & Dialogue System

### 3.1 NPC Roster & Personalities

| NPC | Chinese | Role | Personality | Location(s) |
|-----|---------|------|-------------|-------------|
| Grandma Yan | 焱奶奶 | Flame Tribe elder, forging mentor | Speaks in riddles, laughs at explosions, gives bold/experimental quests | 熔炉谷 (Forge Valley) |
| Grandpa Yuan | 渊爷爷 | Abyss Tribe elder, wisdom keeper | Speaks slowly, tells long stories, asks questions instead of giving answers | 珊瑚城 (Coral City) |
| Little Lie | 小烈 | Yan apprentice, peer character | Enthusiastic, impatient, makes mistakes kids relate to | 熔炉谷, moves with story |
| Little Lan | 小澜 | Yuan apprentice, peer character | Curious, organized, loves cataloging, methodical | 珊瑚城, 百草园 |
| 世界之灵 (World Spirit) | 世界之灵 | Spirit guide / tutorial NPC | Playful, encouraging, explains systems | Everywhere (floating orb) |
| 九尾狐 (Nine-Tailed Fox) | 九尾狐 | Mythical creature NPC | Mischievous, wise, gives illusion puzzles | 青丘山 (Qingqiu Mountain) |
| 白泽 (Baize) | 白泽 | Knowledge keeper | Calm, asks riddles, rewards wisdom | 昆仑山 (Kunlun Mountain) |
| 精卫 (Jingwei) | 精卫 | Persistence teacher | Determined, never gives up, teaches through repetition | 东海 coast |

### 3.2 Quest Types & Structure

**Four primary quest types:**

| Quest Type | Chinese | Description | Example |
|------------|---------|-------------|---------|
| **Fetch** | 收集 | Gather N items of a specific type | "Bring me 5 青木灵叶 for my herbal forge experiment" |
| **Crafting** | 锻造 | Craft a specific item with specific constraints | "Forge a sword using at least 2 火灵 materials" |
| **Exploration** | 探索 | Visit a location, discover something, or restore a faded fragment | "Find the hidden chamber in 石语洞" |
| **Beast Encounter** | 灵兽 | Pacify, capture, or befriend a specific beast | "The 毕方 is causing fires — calm it down" |

**Quest structure (every quest follows this schema):**

```
Quest
├── quest_id: UUID
├── giver_npc_id: UUID
├── title: string
├── title_cn: string
├── quest_type: enum [fetch, crafting, exploration, beast]
├── act: int                    # 1-5, which story act
├── prerequisite_quests: [UUID] # must complete these first
├── prerequisite_conditions: {  # additional requirements
│     player_level: int,
│     fading_meter_min: int,
│     realm_unlocks: [realm_id],
│     items_owned: [{item_id, min_count}]
│   }
├── objectives: [Objective]
├── dialogue_tree_id: UUID      # opening dialogue
├── completion_dialogue_id: UUID
├── rewards: [Reward]
├── fading_meter_change: int    # +1 to +4
├── reputation_change: {        # faction reputation
│     yan_clan: int,
│     yuan_clan: int
│   }
└── is_main_story: bool         # true = blocks story progression
```

**Objective types:**

| Objective Type | Data | Example |
|---------------|------|---------|
| **Collect** | `{material_id, count}` | Collect 5 火灵 materials |
| **Craft** | `{item_type, constraints}` | Craft a fire-element sword |
| **Visit** | `{area_id}` | Visit 石语洞 |
| **Pacify** | `{beast_species_id}` | Pacify a 毕方 |
| **Capture** | `{beast_species_id}` | Capture a 九尾狐 |
| **Restore** | `{fragment_id}` | Restore faded fragment #7 |
| **Dialogue** | `{npc_id, dialogue_branch}` | Talk to Grandpa Yuan about the old days |
| **Breed** | `{offspring_species_id}` | Breed two Mountain beasts |
| **Event_Participate** | `{event_type}` | Participate in a meteor shower |

**Quest difficulty scaling by act:**

| Act | Quest Count | Avg Objectives per Quest | Typical Rewards |
|-----|------------|-------------------------|-----------------|
| 1 | 8-10 | 1-2 | T1 materials, basic recipes, tutorial items |
| 2 | 10-12 | 2-3 | T2 materials, sanctuary unlock, faction reputation |
| 3 | 12-15 | 2-4 | T2-T3 materials, companion abilities, realm keys |
| 4 | 8-10 | 3-5 | T3-T4 materials, story revelations, mirror upgrades |
| 5 | 5-7 | 4-6 | T4-T5 materials, ultimate recipes, story resolution |

### 3.3 Quest Lifecycle

```
┌─────────────┐
│  Available  │  NPC has a quest marker (!) above their head
└──────┬──────┘
       │ Player initiates dialogue
       ▼
┌─────────────┐
│  Accepted   │  Quest appears in journal, objectives tracked
└──────┬──────┘
       │
       ├── Objective progress tracked in real-time
       │   ├── "Collect 青木灵叶: 2/5"
       │   ├── "Craft fire-element sword: 0/1"
       │   └── "Visit 石语洞: Not yet"
       │
       │ Partial completion: journal shows checkmarks
       │ for completed objectives
       │
       ▼
┌─────────────┐
│  Complete   │  All objectives met, quest marker changes to (?)
└──────┬──────┘
       │ Player returns to NPC
       ▼
┌─────────────┐
│  Turned In  │  Dialogue, rewards distributed, fading meter updated
└─────────────┘
```

**Quest tracking UI (HUD):**

```
┌──────────────────────────────────┐
│  当前任务 (Active Quests)        │
│                                  │
│  [Main] 焱奶奶的第一课            │
│    ✓ Collect 火灵 × 3            │
│    ◻ Craft a basic weapon        │
│                                  │
│  [Side] 小澜的材料清单            │
│    ◻ Collect 水灵 × 5 (2/5)      │
│    ◻ Deliver to 小澜             │
│                                  │
│  [Event] ★ 星雨进行中!            │
│    ◻ Collect 3 star fragments     │
└──────────────────────────────────┘
```

**HUD behavior:**
- Maximum 3 quests shown in HUD at once (prevents overwhelm for children)
- Main story quests always shown first
- Event quests shown with a star indicator (time-limited)
- Additional quests accessible via the quest journal
- Quests auto-sort by proximity to completion

### 3.4 Quest Reward Structure

Every quest rewards the player on three axes: **Materials**, **Progression**, and **Story**.

| Reward Type | Examples | Purpose |
|-------------|----------|---------|
| **Materials** | T1-T4 materials, consumables | Immediate utility, enables crafting |
| **Recipes** | New forge recipes, hybrid techniques | Expands player capabilities |
| **Equipment** | Pre-made tools for young players | Helps players who struggle with crafting |
| **灵魄** | 10-200 depending on quest difficulty | Currency for upgrades |
| **Faction Reputation** | +5 to +30 Yan or Yuan reputation | Unlocks faction-specific items |
| **Fading Meter** | +1% to +4% | World progression |
| **Bond XP** | +5 to +20 species bond XP | Companion progression |
| **Story/ Lore** | Codex entries, NPC backstory, world secrets | Narrative satisfaction |
| **Cosmetics** | Titles, weapon skins, sanctuary decorations | Collection and personalization |
| **Unlock Keys** | New areas, new features (sanctuary, breeding) | Progression gates |

**Reward formula:**

```
Base Reward = Quest_Type_Multiplier × Objective_Count × Act_Scale

Where:
  Quest_Type_Multiplier:
    Fetch: 1.0
    Crafting: 1.5
    Exploration: 1.3
    Beast: 1.8

  Act_Scale:
    Act 1: 1.0
    Act 2: 1.5
    Act 3: 2.0
    Act 4: 2.5
    Act 5: 3.0

Material Reward Tier = min(T5, floor(Act_Scale / 1.5) + 1)
# Act 1: T1, Act 2: T2, Act 3: T2-T3, Act 4: T3-T4, Act 5: T4-T5

灵魄 Reward = Base_Reward × 10
# Act 1 fetch quest with 2 objectives: 1.0 × 2 × 1.0 × 10 = 20 灵魄
# Act 3 beast quest with 3 objectives: 1.8 × 3 × 2.0 × 10 = 108 灵魄
```

**Main story quests always give:**
- Fading meter increase (+2-4%)
- A story-relevant codex entry
- At least one realm unlock or story progression item

### 3.5 Dialogue System Architecture

**Dialogue structure: Branching with age-adaptive content.**

```
DialogueTree
├── tree_id: UUID
├── npc_id: UUID
├── nodes: [DialogueNode]
└── global_conditions: {          # conditions affecting all nodes
      player_age_group: enum [6-7, 8-9, 10-12],
      quest_states: {quest_id: status},
      fading_meter: int,
      relationship_level: int     # how well the player knows this NPC
    }

DialogueNode:
├── node_id: UUID
├── speaker: string               # NPC name
├── text: string                  # dialogue text
├── text_alternates: {            # age-adaptive variants
│     "6-7": string,              # simpler language, more emojis
│     "8-9": string,              # standard language
│     "10-12": string             # more complex, hints at deeper lore
│   }
├── portrait: string              # NPC expression/emotion
├── choices: [DialogueChoice]
├── conditions: {                 # when is this node available?
│     min_relationship: int,
│     quest_completed: [UUID],
│     time_of_day: enum [morning, afternoon, evening, night],
│     fading_meter_range: [min, max]
│   }
├── actions: [                    # what happens when this node is reached
│     { type: "give_quest", quest_id: UUID },
│     { type: "give_item", item_id: UUID, count: int },
│     { type: "set_flag", flag: string, value: bool },
│     { type: "change_fading", amount: int },
│   ]
└── next_node: UUID               # default next node if no choice

DialogueChoice:
├── choice_id: UUID
├── text: string
├── text_alternates: { "6-7": string, "8-9": string, "10-12": string }
├── target_node: UUID
├── conditions: { ... }           # same as DialogueNode
└── consequences: [               # what changes when this choice is made
      { type: "flag", flag: string, value: bool },
      { type: "reputation", faction: string, amount: int }
    ]
```

**Dialogue flow example — Grandma Yan giving a quest:**

```
Node 1 (Greeting):
  Yan: "Oh! Little smith! I was just wondering when you'd show up.
        The forge's been acting peculiar today..."
  [text_6_7: "The fire is being silly again! Can you help?"]
  [text_10_12: "The forge flames have been flickering with an
                unusual pattern — almost like they're trying
                to tell us something."]
  Choices:
    A: "What's wrong?" → Node 2
    B: "I'll take a look!" → Node 3 (skip exposition, for impatient kids)

Node 2 (Explanation):
  Yan: "The flames keep turning blue instead of orange! In all my
        years, I've only seen that once — when the old master tried
        to forge with star-metal. Someone must have left 水灵
        materials near the forge..."
  Choices:
    A: "I'll find the 水灵 materials!" → Node 4 (accept quest)
    B: "Can't you just... fix it?" → Node 5

Node 5 (Yan's response to refusal):
  Yan: "Heh! I could, but where's the fun in that? Besides, a good
        smith learns by doing. Now hop to it!"
  → Node 4 (quest still accepted — children's game, no permanent refusal)

Node 4 (Quest Accept):
  Actions: [give_quest: "quench_the_blue_flame"]
  → End
```

**Age-adaptive dialogue rules:**

| Aspect | Ages 6-7 | Ages 8-9 | Ages 10-12 |
|--------|----------|----------|------------|
| **Sentence length** | Short (5-10 words) | Medium (10-20 words) | Full paragraphs |
| **Vocabulary** | Simple words, sound effects | Standard | Includes mythology terms |
| **Hints** | Very explicit ("look near the big tree") | Moderate ("check the forest") | Subtle ("the old growth holds secrets") |
| **Lore depth** | Surface level only | Some backstory | Full mythological context |
| **Choice count** | 2 choices | 2-3 choices | 3-4 choices |
| **Emotional range** | Happy, sad, surprised | + worried, excited | + determined, contemplative |

**NPC daily schedule (dialogue changes by time):**

| NPC | Morning (6-12) | Afternoon (12-18) | Evening (18-22) | Night (22-6) |
|-----|---------------|-------------------|-----------------|--------------|
| Grandma Yan | At the forge, gives crafting quests | Wandering Forge Valley, tells stories | By the fire, gives lore quests | Asleep (interact to wake for rare night quests) |
| Grandpa Yuan | Drinking tea, asks riddles | Cataloging materials at the archive | Stargazing, gives exploration quests | Meditating (rare dialogue about The Fading) |
| Little Lie | Training, gives beginner quests | Exploring, gets into trouble | Playing with beasts, gives beast quests | Asleep |
| Little Lan | Organizing materials, gives fetch quests | In the garden, gives plant quests | Reading codex, gives lore quests | Studying (gives research quests on weekends) |

### 3.6 Quest Journal UI

**Layout concept:**

```
┌────────────────────────────────────────────────────────────┐
│  山海任务簿 (Shanhai Quest Journal)                        │
│                                                            │
│  ┌──────────────┐  ┌────────────────────────────────────┐  │
│  │              │  │  [Main Story]                       │  │
│  │  [Tabs]      │  │  焱奶奶的第一课                     │  │
│  │  ★ 主线      │  │  "Forge your first weapon using     │  │
│  │  ○ 支线      │  │   fire materials from the forge."   │  │
│  │  ◎ 灵兽      │  │                                    │  │
│  │  ◐ 活动      │  │  Progress: ████████░░ 80%          │  │
│  │  ★ 活动      │  │  ✓ Collect 火灵 × 3                │  │
│  │  ☰ 已完成    │  │  ◻ Craft a basic weapon            │  │
│  │              │  │                                    │  │
│  │  Fading:     │  │  [Side Quests]                      │  │
│  │  ██████░░░░  │  │  小澜的材料清单                     │  │
│  │  62%         │  │  "Bring me 5 水灵 materials."      │  │
│  │              │  │  Progress: ████░░░░░░ 40%          │  │
│  │  Active: 3   │  │  ◻ Collect 水灵 × 5 (2/5)          │  │
│  └──────────────┘  └────────────────────────────────────┘  │
│                                                            │
│  [Select quest for details]  [Track]  [Abandon]            │
└────────────────────────────────────────────────────────────┘
```

**Journal features:**

| Feature | Description |
|---------|-------------|
| **Fading meter** | Always visible in the left panel — reminds the player of the overarching goal |
| **Tab filtering** | 6 tabs (Main, Side, Beast, Daily, Event, Completed) |
| **Progress bars** | Visual progress per quest — children see how close they are |
| **Objective checkboxes** | Clear checkmarks for completed objectives |
| **Tracking** | "Track" button puts a quest in the HUD (max 3 tracked) |
| **Abandon** | Can abandon side quests (main story quests cannot be abandoned) |
| **Hints** | "Need help?" button on each quest gives an age-appropriate hint |
| **Completed tab** | Shows finished quests with rewards earned — serves as an achievement log |

**Age-adaptive journal:**

| Feature | Ages 6-7 | Ages 8-9 | Ages 10-12 |
|---------|----------|----------|------------|
| **Tab count** | 3 (Main, Side, Completed) | 5 (adds Beast, Event) | 6 (adds Daily) |
| **Quest descriptions** | Icon + 1 sentence | 2-3 sentences | Full description |
| **Hint system** | Auto-hints after 2 min of inactivity | Manual "hint" button | "Hint" costs 5 灵魄 |
| **Visual style** | Large icons, bright colors | Standard | More text, compact layout |

### 3.7 NPC Quests Tied to "The Fading" Storyline

Each NPC's quest chain contributes to the main narrative about The Fading. The quests are structured as **parallel threads** that converge at key story beats.

**Story thread mapping:**

```
Act 1: The Shattered Mirror
├── Grandma Yan thread: "The forge fires are dying"
│     → Yan teaches forging basics
│     → Reveals that forge fires are connected to world vitality
│     → Quest chain reward: Basic forging ability, +3% Fading
│
├── Grandpa Yuan thread: "The coral is losing its color"
│     → Yuan teaches material analysis
│     → Reveals that materials are losing their spirit
│     → Quest chain reward: Material codex access, +3% Fading
│
├── Little Lie thread: "I want to help but I keep messing up!"
│     → Teaches that mistakes are part of learning
│     → Player helps Lie complete a (failed) forging attempt
│     → Quest chain reward: Lie's "Try Again" buff (+10% forge retry), +2% Fading
│
└── Little Lan thread: "I've been cataloging — something is wrong"
      → Lan shows data: beast encounters are down 30%
      → Player investigates a faded fragment
      → Quest chain reward: First faded fragment restored, +5% Fading

Act 2: First Sparks
├── Yan: "The old ways aren't enough — we need something new"
│     → Introduces hybrid crafting (Yan + Yuan techniques)
│
├── Yuan: "Perhaps... the Yan tribe was right about one thing"
│     → Yuan admits change is sometimes necessary
│
├── Lie: "I caught my first beast! Well, it caught itself..."
│     → Introduces companion system, sanctuary unlock
│
└── Lan: "The fragments are connected — restoring one helps others"
      → Reveals the network of faded fragments

Act 3: The Living World
├── Yan + Yuan joint quest: "The Great Forge Contest"
│     → Player crafts for both tribes simultaneously
│     → Tribes begin to reconcile
│
├── Lie: "My beast friend is sad — the world is getting grey"
│     → Companion-focused quest chain, bond level milestones
│
└── Lan: "I found a pattern — The Fading follows the World River"
      → Player follows the river to its source

Act 4: The Truth
├── All NPCs: Journey to the Dream Realm
├── Revelation: The Fading is caused by forgotten stories
│     → NPCs share their stories, each one restores a fragment
├── The Mirror reveals its full power
└── Player must choose: restore the world as it was, or create something new

Act 5: The Great Forge
├── All NPCs contribute to the Ultimate Artifact
├── Yan provides fire, Yuan provides water, Lie provides courage,
│     Lan provides knowledge, companions provide spirit
└── Player forges the artifact that reconnects the Five Realms
```

**Fading-related quest markers in dialogue:**

| Fading Meter Range | NPC Dialogue Tone |
|-------------------|-------------------|
| 70-100% | Normal, optimistic |
| 50-70% | Slightly concerned, mentions "feeling off" |
| 30-50% | Worried, some NPCs become unavailable (retreated) |
| 10-30% | Urgent, NPCs give desperate pleas for help |
| <10% (crisis) | NPCs gather at the World Tree, give the "last hope" quest |

### 3.8 Data Structures

```yaml
Quest:
  quest_id: UUID
  giver_npc_id: UUID
  title: string
  title_cn: string
  quest_type: enum [fetch, crafting, exploration, beast]
  act: int                        # 1-5
  is_main_story: bool
  prerequisite_quests: [UUID]
  prerequisites: {
    player_level_min: int,
    fading_meter_min: int,
    realm_unlocks: [realm_id],
    bond_level_min: {species_id: int},
  }
  objectives: [QuestObjective]
  rewards: [QuestReward]
  fading_meter_change: int        # +1 to +4
  reputation_change: { yan: int, yuan: int }
  dialogue_tree_id: UUID

QuestObjective:
  type: enum [collect, craft, visit, pacify, capture, restore,
              dialogue, breed, event_participate]
  target_id: UUID                 # material_id, area_id, beast_id, etc.
  count: int                      # required count (1 for most types)
  current_progress: int           # tracked in real-time
  completed: bool

QuestReward:
  type: enum [material, recipe, equipment, currency, reputation,
              bond_xp, codex, cosmetic, unlock_key, fading_meter]
  item_id: UUID                   # references the reward item
  amount: int                     # quantity
  tier: int                       # material/equipment tier

NPCState:
  npc_id: UUID
  relationship_level: int         # 0-10, increases with quest completions
  quests_given: [UUID]
  quests_completed_by_player: [UUID]
  current_location: area_id
  schedule_state: enum [morning, afternoon, evening, night]
  dialogue_flags: {string: bool}  # persistent conversation state
  fading_reactions_triggered: [range]  # which fading meter reactions shown

QuestJournal:
  player_id: UUID
  active_quests: [UUID]           # quest IDs currently in progress
  completed_quests: [UUID]        # quest IDs finished
  tracked_quests: [UUID]          # max 3, shown in HUD
  quest_progress: {
    quest_id: {
      objective_index: {current: int, completed: bool}
    }
  }
```

---

## 4. Cross-System Integration

These three systems do not operate in isolation. Here is how they interconnect:

### 4.1 System Interaction Map

```
                    ┌─────────────────────┐
                    │   The Fading Meter   │
                    │   (Central Hub)      │
                    └──────────┬──────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
    ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
    │  Companion    │  │    Events     │  │  NPC Quests   │
    │  System       │  │    System     │  │  System       │
    └───────┬───────┘  └───────┬───────┘  └───────┬───────┘
            │                  │                  │
            │                  │                  │
      ┌─────┼──────────────────┼──────────────────┼─────┐
      │     │                  │                  │     │
      ▼     ▼                  ▼                  ▼     ▼
    Bond   Spirit            Event             Quest
    XP↑    Tide              rewards           types:
    during                   include           - Beast
    Spirit                   companion         - Craft
    Tide                     encounters        - Explore
                                                 - Fetch

Specific integrations:
  1. NPC quests GIVE companions (Little Lie's introduction quest)
  2. Events SPAWN rare beasts for capture (Spirit Tide, Aurora Veil)
  3. Companion bond level UNLOCKS new NPC dialogue options
  4. The Fading meter AFFECTS quest availability (urgent quests at low meter)
  5. Festival events give QUEST CHAINS (3-5 linked quests)
  6. Beast encounters ARE quest objectives (type: beast)
  7. Breeding requires materials from EVENT rewards
  8. World boss defeat RESTORES fading meter significantly (+3-5%)
  9. NPC relationship level AFFECTS event participation rewards (+5% per level)
  10. Companion abilities help complete EXPLORATION quest objectives
```

### 4.2 Integration Details

**Integration 1: Companion as quest reward**
- Little Lie's Act 2 quest "我的第一个朋友" rewards the player with a starter companion
- The companion is a level 1 狸力 (Lili, a digging creature) with pre-set bond level 1
- This introduces the companion system organically through narrative

**Integration 2: Event-exclusive beast encounters**
| Event | Exclusive Beast | Capture Difficulty |
|-------|----------------|-------------------|
| Spirit Tide | 灵潮兽 (Tide Beast) — elemental variant | ★★ |
| Aurora Veil | 极光灵 (Aurora Spirit) — UR mutation chance | ★★★ |
| Meteor Shower | 星陨兽 (Starfall Beast) — 火灵 type | ★★ |
| Dragon Boat | 龙舟灵 (Dragon Boat Spirit) — festival companion | ★ |
| Mid-Autumn | 月兔 (Moon Rabbit) — temporary 7-day companion | ★ |

**Integration 3: Bond level unlocking NPC dialogue**
| Bond Level | NPC | Unlock |
|------------|-----|--------|
| 3 (any species) | Grandpa Yuan | Asks about your companion, gives lore about the species' origin in 山海经 |
| 5 (any species) | Grandma Yan | "That beast of yours has spirit! Let me forge it a special charm." Gives a permanent +5% damage buff to that species |
| 7 (any species) | Nine-Tailed Fox | Appears as an NPC, offers illusion-based quests |
| 10 (any species) | World Spirit | "Your bond is legendary!" Unlocks the "Eternal Bond" achievement and a permanent +1% Fading meter floor |

**Integration 4: Fading meter affecting quest availability**
| Fading Range | Effect on Quests |
|--------------|-----------------|
| 50-70% | Standard quest pool |
| 30-50% | "Urgent" quests become available (higher rewards, time-limited) |
| 10-30% | Normal quests暂停; only "Crisis Response" quests available |
| <10% | Single "Last Hope" quest chain from all NPCs converging |

**Integration 5: Festival quest chains**
Each festival triggers a 3-5 quest chain:
```
Spring Festival Chain:
  1. [Fetch] Collect red materials (火灵 × 5) → Grandma Yan
  2. [Craft] Forge a red weapon → Forge
  3. [Beast] Scare away small Nian scouts → Combat
  4. [Event] Participate in New Year celebration → Mini-game
  5. [Boss] Defeat the Nian Beast → Multi-phase combat

Dragon Boat Chain:
  1. [Craft] Build a dragon boat → Crafting mini-game
  2. [Event] Win 2 races → Racing mini-game
  3. [Explore] Navigate the river maze → Puzzle
  4. [Beast] Befriend the Zongzi Spirit → Pacify

Mid-Autumn Chain:
  1. [Explore] Find 3 hidden mooncakes → Dream Realm exploration
  2. [Craft] Place 5 lanterns → Spatial puzzle
  3. [Dialogue] Answer Moon Rabbit's riddles → Riddle mini-game
  4. [Beast] Spend time with Moon Rabbit companion → Bond XP event
```

**Integration 6: Beast encounters as quest objectives**
- 30% of all quests have a beast encounter as one of their objectives
- Beast quests scale with the player's companion bond level (higher bond = easier encounter)
- Completing a beast quest with a companion at bond level 5+ gives bonus rewards

**Integration 7: Event materials for breeding**
- T3 materials from events are used as breeding catalysts
- Festival-exclusive materials (年兽角, 龙舟鳞, 月光玉) can trigger special mutations when used in breeding
- Breeding during a Spirit Tide event has +15% spontaneous mutation chance

**Integration 8: World boss → Fading restoration**
- Each world boss defeat restores 3-5% of the Fading meter
- The restored areas become visually vibrant again (grey → color transition animation)
- NPCs in restored areas gain new dialogue and new quests

**Integration 9: NPC relationship → Event bonus**
- For each relationship level with any NPC (0-10), event participation rewards increase by 5%
- At relationship level 5+, NPCs may join the player during world boss fights as support characters
- At relationship level 8+, NPCs share "secret" event locations

**Integration 10: Companion abilities for exploration quests**
- Companions with specific elements can unlock exploration shortcuts:
  - 火 element: Burns away grey mist blocking paths (Fading-related obstacles)
  - 水 element: Creates temporary bridges over water gaps
  - 木 element: Grows vines to climb otherwise inaccessible areas
  - 金 element: Breaks through cracked stone walls
  - 土 element: Detects hidden material caches underground

---

*Document version: 1.0 | Realmforge Design Team | 2026-04-09*
