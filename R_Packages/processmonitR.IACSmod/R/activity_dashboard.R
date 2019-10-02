


#' Activity Dashboard
#'
#' @param eventlog Event log to be used for dashboard
#'
#' @export
#'
activity_dashboard <- function(eventlog) {

	ui <- miniPage(
		gadgetTitleBar("Activity dashboard"),
		miniContentPanel(
			fillCol(
				navbarPage("",
						   tabPanel("Activity Frequency",
						   		 plotOutput("activity_frequency")
						   ),
						   tabPanel("Activity Presence",
						   		 plotOutput("activity_presence")
						   )
				)

			)

		)
	)



	server <- function(input, output, session){

		output$activity_frequency <- renderPlot({
			eventlog %>%
				activity_frequency("activity") %>%
				plot()
		})
		output$activity_presence <- renderPlot({
			eventlog %>%
				activity_presence() %>%
				plot()
		})


		observeEvent(input$done, {
			stopApp()
		})
	}

	runGadget(shinyApp(ui, server), viewer = dialogViewer("Activity dashboard", height = 900, width = 1200))

}
