from shiny import App, ui, Inputs, Outputs, Session


app_ui = ui.page_fluid(
    ui.head_content(ui.tags.link(rel="icon", type="image/x-icon", href="")),
    ui.include_css("./www/styles.css"),
    ui.h2("Hello World")
)

def server(input: Inputs, output: Outputs, session: Session):
    pass


paift_run_details = App(app_ui, server)