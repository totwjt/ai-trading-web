```markdown
# Design System Document: Precision Fintech Editorial

## 1. Overview & Creative North Star
### Creative North Star: "The Informed Architect"
In the world of high-stakes Chinese equity trading, the difference between a "retail app" and a "professional terminal" is the mastery of information density. This design system moves beyond the cluttered, chaotic grids of traditional platforms like East Money. Instead, it adopts the persona of **The Informed Architect**: a system that organizes massive data sets through sophisticated tonal layering, surgical typography, and intentional white space.

The goal is to provide a "Bloomberg-level" authority using a high-end editorial approach. We break the "template" look by eschewing traditional 1px borders in favor of **Tonal Partitioning**—using subtle shifts in background values to define data clusters, creating a UI that feels like a single, cohesive instrument rather than a collection of boxes.

---

## 2. Colors & Surface Logic

### The Palette
We utilize a sophisticated Material-based expansion of the core brand colors to ensure depth.
- **Primary Blue (`#0050cb`)**: The color of institutional trust. Used for primary actions and focused data points.
- **Secondary Red (`#bb0018`) / Tertiary Green (`#236700`)**: Following Chinese market conventions (Red = Up, Green = Down). These are high-chroma for instant recognition but grounded by their container variants.

### The "No-Line" Rule
**Strict Mandate:** Designers are prohibited from using 1px solid borders to section off content. 
Structure must be achieved through:
1.  **Background Shifts:** Place a `surface_container_lowest` card on a `surface_container_low` background.
2.  **Negative Space:** Use the `2.5 (0.5rem)` or `3 (0.6rem)` spacing tokens to create logical groupings.
3.  **Tonal Transitions:** Use `surface_variant` for subtle headers that bleed into the background.

### Surface Hierarchy & Nesting
Treat the UI as a series of stacked, precision-cut sheets:
- **Base Layer:** `surface` (`#f7f9fc`) - The workspace.
- **Content Blocks:** `surface_container_lowest` (`#ffffff`) - The primary canvas for data tables and charts.
- **Hover/Active States:** `surface_container_high` (`#e6e8eb`) - To indicate depth upon interaction.

### The "Glass & Gradient" Rule
To elevate the platform above "standard fintech," use **Glassmorphism** for floating utility panels (e.g., quick-buy drawers or tooltips). Use a `surface_container_lowest` color at 85% opacity with a `20px` backdrop-blur. 
*Signature Polish:* Main CTAs should use a subtle linear gradient from `primary` to `primary_container` to give buttons a "milled" metallic feel.

---

## 3. Typography: The Editorial Grid
We use **Inter** for numerals and **PingFang SC** for Chinese characters to ensure maximum legibility at small sizes.

| Level | Token | Size | Usage |
| :--- | :--- | :--- | :--- |
| **Display** | `display-sm` | 2.25rem | Portfolio total balance (Hero numbers). |
| **Headline** | `headline-sm` | 1.5rem | Sector names or major market indices. |
| **Title** | `title-sm` | 1rem | Card headers; bold for emphasis. |
| **Body** | `body-md` | 0.875rem | Standard data labels and news snippets. |
| **Label** | `label-sm` | 0.6875rem | "Micro-data" (e.g., P/E ratios, timestamps). |

**Editorial Intent:** Use `label-sm` in `on_surface_variant` (`#424656`) for metadata to create high contrast against `title-sm` stock names. This "High-Low" pairing allows users to scan 50+ rows of data without eye fatigue.

---

## 4. Elevation & Depth: Tonal Layering

### The Layering Principle
Forget shadows for standard cards. Achieve hierarchy by nesting:
- **Level 0 (App Background):** `surface`
- **Level 1 (Market Overview Card):** `surface_container_lowest`
- **Level 2 (Internal Data Cells):** `surface_container_low`

### Ambient Shadows
When an element must "float" (e.g., a stock search modal), use an **Ambient Shadow**:
- `box-shadow: 0 12px 32px -4px rgba(25, 28, 30, 0.08);`
The shadow color is derived from `on_surface`, ensuring it looks like a natural occlusion of light rather than a "drop shadow" effect.

### The "Ghost Border" Fallback
If a data table requires a separator for accessibility, use a **Ghost Border**:
- Color: `outline_variant` (`#c2c6d8`)
- Opacity: **15%**
- Width: `1px`
This creates a "suggestion" of a line that disappears into the background upon quick glance.

---

## 5. Components: Precision Instruments

### Cards & Lists
*   **Requirement:** Forbid divider lines between list items.
*   **The Alternative:** Use a `1px` gap between `surface_container_lowest` rows, allowing the `surface_container_low` background to peek through, creating a natural separator.
*   **Spacing:** Use `3 (0.6rem)` padding for high-density lists.

### Buttons
*   **Primary:** `primary` background, `on_primary` text. Radius: `md (0.375rem)`.
*   **Tertiary (The "Data" Button):** No background. Use `primary` text. Used for "View More" actions within dense tables.

### Input Fields
*   **Style:** Minimalist. No bottom line. Use `surface_container_highest` as a solid background fill with a `sm (0.125rem)` radius. 
*   **Focus State:** A `2px` `primary` "Ghost Border" at 40% opacity.

### Financial Chips (Status Indicators)
*   **Bullish:** `secondary_container` background with `on_secondary_container` text.
*   **Bearish:** `tertiary_container` background with `on_tertiary_container` text.
*   **Shape:** `DEFAULT (0.25rem)` radius for a technical, "tag-like" feel.

---

## 6. Do's and Don'ts

### Do:
*   **Embrace Density:** Use `label-sm` for secondary data. Professional traders prefer more data on one screen over "clean" empty space.
*   **Use Tonal Shifts:** If a section feels "lost," change its background color to `surface_container_low` instead of adding a border.
*   **Color as Data:** Only use `secondary` (Red) and `tertiary` (Green) for price movement. Never use them for decorative UI elements.

### Don't:
*   **No Heavy Shadows:** Never use shadows on standard cards. It creates visual "muck" in high-density layouts.
*   **No Rounded Corners > 8px:** Avoid `xl` or `full` rounding for anything other than buttons or search bars. Large radii feel too "consumer/social" for a trading platform.
*   **No Pure Black:** Never use `#000000`. Always use `on_surface` (`#191c1e`) to maintain the sophisticated, editorial ink-on-paper feel.

---
**Director’s Final Note:** 
This system is a tool of precision. Every pixel should feel like it was placed by a Swiss watchmaker. If a layout feels "busy," do not remove data—increase the sophistication of the tonal layering.```