"""Simple placeholder SDG goal icons (coloured square with the goal number).

The official UN SDG icons are not redistributed here; SDG Tag Heroes only needs some SVG per goal.
"""

from .sdgs import SDG


def goal_icon(sdg: SDG) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" fill="{sdg.color}"/>
  <text x="50" y="62" font-family="Arial, Helvetica, sans-serif" font-size="44" font-weight="bold"
        fill="#ffffff" text-anchor="middle">{sdg.id}</text>
</svg>
"""
