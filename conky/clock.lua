package.cpath = package.cpath .. ';/usr/lib/conky/?.so'
require 'cairo'
require 'cairo_xlib'

local function draw_clock_face()
    if conky_window == nil then
        return
    end

    local cs = cairo_xlib_surface_create(
        conky_window.display, conky_window.drawable, conky_window.visual,
        conky_window.width, conky_window.height
    )
    local cr = cairo_create(cs)

    local r = 90
    local cx, cy = conky_window.width / 2, r + 10

    -- face outline
    cairo_set_source_rgba(cr, 1, 1, 1, 0.9)
    cairo_set_line_width(cr, 3.5)
    cairo_arc(cr, cx, cy, r, 0, 2 * math.pi)
    cairo_stroke(cr)

    -- tick marks
    for i = 0, 11 do
        local ang = i * (math.pi / 6)
        local outer = r - 7
        local len = (i % 3 == 0) and 14 or 7
        local x1 = cx + outer * math.sin(ang)
        local y1 = cy - outer * math.cos(ang)
        local x2 = cx + (outer - len) * math.sin(ang)
        local y2 = cy - (outer - len) * math.cos(ang)
        cairo_set_line_width(cr, (i % 3 == 0) and 3.5 or 2)
        cairo_set_source_rgba(cr, 1, 1, 1, (i % 3 == 0) and 0.85 or 0.5)
        cairo_move_to(cr, x1, y1)
        cairo_line_to(cr, x2, y2)
        cairo_stroke(cr)
    end

    local hh = tonumber(os.date('%I'))
    local mm = tonumber(os.date('%M'))
    local ss = tonumber(os.date('%S'))

    local hour_ang = ((hh % 12) + mm / 60) * (math.pi / 6)
    local min_ang = (mm + ss / 60) * (math.pi / 30)
    local sec_ang = ss * (math.pi / 30)

    -- hour hand
    cairo_set_source_rgba(cr, 1, 1, 1, 0.95)
    cairo_set_line_width(cr, 5)
    cairo_move_to(cr, cx, cy)
    cairo_line_to(cr, cx + r * 0.5 * math.sin(hour_ang), cy - r * 0.5 * math.cos(hour_ang))
    cairo_stroke(cr)

    -- minute hand
    cairo_set_line_width(cr, 4)
    cairo_move_to(cr, cx, cy)
    cairo_line_to(cr, cx + r * 0.75 * math.sin(min_ang), cy - r * 0.75 * math.cos(min_ang))
    cairo_stroke(cr)

    -- second hand
    cairo_set_source_rgba(cr, 0.75, 0.75, 0.75, 0.85)
    cairo_set_line_width(cr, 2)
    cairo_move_to(cr, cx, cy)
    cairo_line_to(cr, cx + r * 0.85 * math.sin(sec_ang), cy - r * 0.85 * math.cos(sec_ang))
    cairo_stroke(cr)

    -- center dot
    cairo_set_source_rgba(cr, 1, 1, 1, 1)
    cairo_arc(cr, cx, cy, 4.5, 0, 2 * math.pi)
    cairo_fill(cr)

    cairo_destroy(cr)
    cairo_surface_destroy(cs)
end

local function centered_text(cr, cx, y, text)
    local ext = cairo_text_extents_t:create()
    cairo_text_extents(cr, text, ext)
    cairo_move_to(cr, cx - ext.width / 2 - ext.x_bearing, y)
    cairo_show_text(cr, text)
end

-- Single self-contained block: header + rings + labels, so it can never drift
-- out of sync with the surrounding conky.text flow.
local SYSTEM_BLOCK_TOP = 423

local function draw_system_block()
    if conky_window == nil then
        return
    end

    local cs = cairo_xlib_surface_create(
        conky_window.display, conky_window.drawable, conky_window.visual,
        conky_window.width, conky_window.height
    )
    local cr = cairo_create(cs)

    local w = conky_window.width
    local top = SYSTEM_BLOCK_TOP

    -- "SYSTEM" header
    cairo_select_font_face(cr, "Noto Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL)
    cairo_set_font_size(cr, 9)
    cairo_set_source_rgba(cr, 1, 1, 1, 1)
    centered_text(cr, w / 2, top, "SYSTEM")

    local stats = {
        { label = "CPU", value = tonumber(conky_parse("${cpu cpu0}")) or 0 },
        { label = "RAM", value = tonumber(conky_parse("${memperc}")) or 0 },
        { label = "DISK", value = tonumber(conky_parse("${fs_used_perc /}")) or 0 },
        { label = "BATT", value = tonumber(conky_parse("${battery_percent BAT0}")) or 0 },
    }

    local ring_r = 14
    local ring_cy = top + 12 + ring_r + 4

    for i, s in ipairs(stats) do
        local cx = (w / #stats) * (i - 0.5)
        local pct = math.max(0, math.min(100, s.value))

        cairo_set_source_rgba(cr, 1, 1, 1, 0.15)
        cairo_set_line_width(cr, 4)
        cairo_arc(cr, cx, ring_cy, ring_r, 0, 2 * math.pi)
        cairo_stroke(cr)

        local start_ang = -math.pi / 2
        local end_ang = start_ang + (pct / 100) * 2 * math.pi
        cairo_set_source_rgba(cr, 1, 1, 1, 0.95)
        cairo_set_line_width(cr, 4)
        cairo_arc(cr, cx, ring_cy, ring_r, start_ang, end_ang)
        cairo_stroke(cr)

        cairo_select_font_face(cr, "Noto Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL)
        cairo_set_font_size(cr, 9)
        local txt = tostring(math.floor(pct)) .. "%"
        local ext = cairo_text_extents_t:create()
        cairo_text_extents(cr, txt, ext)
        cairo_set_source_rgba(cr, 1, 1, 1, 0.95)
        cairo_move_to(cr, cx - ext.width / 2 - ext.x_bearing, ring_cy - ext.height / 2 - ext.y_bearing)
        cairo_show_text(cr, txt)

        -- label, directly under its own ring
        cairo_select_font_face(cr, "Noto Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL)
        cairo_set_font_size(cr, 8)
        cairo_set_source_rgba(cr, 0.67, 0.67, 0.67, 1)
        centered_text(cr, cx, ring_cy + ring_r + 14, s.label)
    end

    cairo_destroy(cr)
    cairo_surface_destroy(cs)
end

function conky_draw_clock()
    draw_clock_face()
    draw_system_block()
end
