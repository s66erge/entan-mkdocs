from fasthtml.common import *

app, rt = fast_app()

# Color table
colors = [
    {"id": 1, "name": "Red"},
    {"id": 2, "name": "Blue"},
    {"id": 3, "name": "Green"},
    {"id": 4, "name": "Yellow"},
    {"id": 5, "name": "Purple"},
]

# Sample data
items = [
    {"id": 1, "name": "Item 1", "price": "$10", "color": "Red"},
    {"id": 2, "name": "Item 2", "price": "$20", "color": "Blue"},
    {"id": 3, "name": "Item 3", "price": "$30", "color": "Green"},
    {"id": 4, "name": "Item 4", "price": "$40", "color": "Yellow"},
]

next_id = 5


def get_color_options(selected_color=None):
    """Generate color options for select dropdown."""
    return [Option(c["name"], value=c["name"], selected=(c["name"] == selected_color)) for c in colors]


@rt("/")
def home():
    return Html(
        Head(Title("FastHTML HTMX Table")),
        Body(
            H1("Edit Table Row"),
            Table(
                Thead(Tr(Th("Name"), Th("Price"), Th("Color"), Th("Action"))),
                Tbody(
                    *[Tr(
                        Td(item["name"], id=f"name-{item['id']}"),
                        Td(item["price"], id=f"price-{item['id']}"),
                        Td(item["color"], id=f"color-{item['id']}"),
                        Td(
                            Button("Edit", hx_get=f"/edit/{item['id']}", hx_target=f"#row-{item['id']}", hx_swap="outerHTML"),
                            " ",
                            Button("Delete", hx_get=f"/delete_confirm/{item['id']}", hx_target=f"#row-{item['id']}", hx_swap="outerHTML", cls="danger")
                        ),
                        id=f"row-{item['id']}"
                    ) for item in items],
                    id="table-body"
                )
            ),
            H2("Add New Item"),
            Div(
                Button("Show Form", hx_get="/add_form", hx_target="#add-form-container", hx_swap="innerHTML"),
                Div(id="add-form-container"),
                id="add-section"
            ),
            Hr(),
            H2("Available Colors"),
            Table(
                Thead(Tr(Th("Color Name"))),
                Tbody(
                    *[Tr(Td(color["name"])) for color in colors]
                )
            ),
            Script(src="https://unpkg.com/htmx.org")
        )
    )

@rt("/add_form")
def add_form():
    """Show the add item form."""
    return Form(
        Div(
            Label("Name:", For="new-name"),
            Input(type="text", name="name", id="new-name", required=True),
        ),
        Div(
            Label("Price:", For="new-price"),
            Input(type="text", name="price", id="new-price", required=True),
        ),
        Div(
            Label("Color:", For="new-color"),
            Select(
                Option("Select a color", value="", disabled=True, selected=True),
                *get_color_options(),
                name="color",
                id="new-color",
                required=True
            ),
        ),
        Div(
            Button("Add Item", type="submit"),
            " ",
            Button("Cancel", type="button", hx_get="/clear_form", hx_target="#add-form-container", hx_swap="innerHTML")
        ),
        hx_post="/add_item",
        hx_target="#table-body",
        hx_swap="beforeend"
    )

@rt("/clear_form")
def clear_form():
    """Clear the add form."""
    return ""

@rt("/add_item", methods=["POST"])
async def add_item(request):
    """Add a new item to the table."""
    global items, next_id
    form_data = await request.form()
    name = form_data.get("name") or ""
    price = form_data.get("price") or ""
    color = form_data.get("color") or ""
    
    # Validate color
    valid_colors = [c["name"] for c in colors]
    if color not in valid_colors:
        return Div(P("Invalid color selected.", style="color: red;"))
    
    if name and price and color:
        new_item = {"id": next_id, "name": name, "price": price, "color": color}
        items.append(new_item)
        next_id += 1

        # Return the new row HTML
        return Tr(
            Td(new_item["name"], id=f"name-{new_item['id']}"),
            Td(new_item["price"], id=f"price-{new_item['id']}"),
            Td(new_item["color"], id=f"color-{new_item['id']}"),
            Td(
                Button("Edit", hx_get=f"/edit/{new_item['id']}", hx_target=f"#row-{new_item['id']}", hx_swap="outerHTML"),
                " ",
                Button("Delete", hx_get=f"/delete_confirm/{new_item['id']}", hx_target=f"#row-{new_item['id']}", hx_swap="outerHTML", cls="danger")
            ),
            Div("", hx_swap_oob="true", id="add-form-container"),
            id=f"row-{new_item['id']}"
        )
    
    return ""

@rt("/edit/{item_id}")
def edit_row(item_id: int):
    item = next((i for i in items if i["id"] == int(item_id)), None)
    if not item:
        return ""
    
    return Tr(
        Td(Input(type="text", name="name", value=item["name"], id=f"edit-name-{item_id}")),
        Td(Input(type="text", name="price", value=item["price"], id=f"edit-price-{item_id}")),
        Td(
            Select(
                *get_color_options(item["color"]),
                name="color",
                id=f"edit-color-{item_id}"
            )
        ),
        Td(
            Button("Confirm", type="button", hx_post=f"/confirm/{item_id}", hx_include=f"#edit-row-{item_id}", hx_target=f"#edit-row-{item_id}", hx_swap="outerHTML"),
            " ",
            Button("Cancel", type="button", hx_get=f"/cancel/{item_id}", hx_target=f"#edit-row-{item_id}", hx_swap="outerHTML")
        ),
        id=f"edit-row-{item_id}"
    )

@rt("/confirm/{item_id}", methods=["POST"])
async def confirm_edit(item_id: int, request):
    """Extract form data from request and update item."""
    form_data = await request.form()
    name = form_data.get("name") or ""
    price = form_data.get("price") or ""
    color = form_data.get("color") or ""
    
    # Validate color
    valid_colors = [c["name"] for c in colors]
    if color not in valid_colors:
        return Div(P("Invalid color selected.", style="color: red;"))
    
    item = next((i for i in items if i["id"] == int(item_id)), None)
    if item:
        item["name"] = name
        item["price"] = price
        item["color"] = color
    
    return Tr(
        Td(item["name"], id=f"name-{item_id}"),
        Td(item["price"], id=f"price-{item_id}"),
        Td(item["color"], id=f"color-{item_id}"),
        Td(
            Button("Edit", hx_get=f"/edit/{item_id}", hx_target=f"#row-{item_id}", hx_swap="outerHTML"),
            " ",
            Button("Delete", hx_get=f"/delete_confirm/{item_id}", hx_target=f"#row-{item_id}", hx_swap="outerHTML", cls="danger")
        ),
        id=f"row-{item_id}"
    )

@rt("/cancel/{item_id}")
def cancel_edit(item_id: int):
    """Cancel editing and return to display mode."""
    item = next((i for i in items if i["id"] == int(item_id)), None)
    if not item:
        return ""
    
    return Tr(
        Td(item["name"], id=f"name-{item_id}"),
        Td(item["price"], id=f"price-{item_id}"),
        Td(item["color"], id=f"color-{item_id}"),
        Td(
            Button("Edit", hx_get=f"/edit/{item_id}", hx_target=f"#row-{item_id}", hx_swap="outerHTML"),
            " ",
            Button("Delete", hx_get=f"/delete_confirm/{item_id}", hx_target=f"#row-{item_id}", hx_swap="outerHTML", cls="danger")
        ),
        id=f"row-{item_id}"
    )

@rt("/delete_confirm/{item_id}")
def delete_confirm(item_id: int):
    """Show confirmation dialog for delete."""
    return Tr(
        Td("Are you sure?", colspan=3),
        Td(
            Button("Yes, Delete", hx_post=f"/delete/{item_id}", hx_target=f"#row-{item_id}", hx_swap="outerHTML swap:1s", style="background-color: red;"),
            " ",
            Button("No, Cancel", hx_get=f"/cancel/{item_id}", hx_target=f"#row-{item_id}", hx_swap="outerHTML")
        ),
        id=f"row-{item_id}"
    )

@rt("/delete/{item_id}", methods=["POST"])
async def delete_item(item_id: int):
    """Delete item and remove row from table."""
    global items
    items = [i for i in items if i["id"] != int(item_id)]
    return ""

serve()