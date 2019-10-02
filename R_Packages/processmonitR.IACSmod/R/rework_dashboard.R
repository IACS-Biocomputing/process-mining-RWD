


#' Rework Dashboard
#'
#' @param eventlog Event log to be used for dashboard
#'
#' @export
#'
rework_dashboard <- function(eventlog) {

	ui <- miniPage(
		gadgetTitleBar("Rework dashboard"),
		miniContentPanel(
			fillCol(
				navbarPage("",
						   tabPanel("Selfloops",
						   		 plotOutput("selfloops_matrix")
						   ),
						   tabPanel("Repetitions",
						   		 plotOutput("repetitions_matrix")
						   )
				)

			)

		)
	)



	server <- function(input, output, session){

		output$selfloops_matrix <- renderPlot({
			eventlog %>%
				redo_selfloops_referral_matrix() %>%
				plot()
		})
		output$repetitions_matrix <- renderPlot({
			eventlog %>%
				redo_repetitions_referral_matrix() %>%
				plot()
		})


		observeEvent(input$done, {
			stopApp()
		})
	}

	runGadget(shinyApp(ui, server), viewer = dialogViewer("Rework dashboard", height = 900, width = 1200))

}
