
def positions_occupied(item):
    x = item.get_position_x()
    y = item.get_position_y()

    return {
        (x + dx, y + dy)
        for dx in range(item.get_width())
        for dy in range(item.get_height())
    }

def validate_feasibility(slices, bin_width, bin_height, objective_value):
    occupied = set()
    total_items = 0
    for slice_ in slices:
        for item in slice_.get_items():
            cells_item = positions_occupied(item)
            assert all(0 <= x < bin_width for x, y in cells_item)
            assert all(0 <= y < bin_height for x, y in cells_item)
            assert occupied.isdisjoint(cells_item)
            occupied.update(cells_item)
            total_items += 1
    assert total_items == objective_value
