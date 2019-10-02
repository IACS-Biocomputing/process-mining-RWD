


#' Resource Dashboard
#'
#' @param eventlog Event log to be used for dashboard
#'
#' @export
#'
resource_dashboard <- function(eventlog) {

	ui <- miniPage(
		gadgetTitleBar("Resource dashboard"),
		miniContentPanel(
			fillCol(
				navbarPage("",
						   tabPanel("Resource frequency",
						   		 navlistPanel(well = F,widths = c(2,9),
						   		 			 tabPanel("Log",
						   		 			 		 plotOutput("resource_frequency_log")
						   		 			 ),
						   		 			 tabPanel("Case",
						   		 			 		 plotOutput("resource_frequency_case")
						   		 			 ),
						   		 			 tabPanel("Resource",
						   		 			 		 plotOutput("resource_frequency_resource")
						   		 			 ),
						   		 			 tabPanel("Activity",
						   		 			 		 plotOutput("resource_frequency_activity")
						   		 			 ),
						   		 			 tabPanel("Resource-activity",
						   		 			 		 plotOutput("resource_frequency_resource_activity")
						   		 			 )
						   		 )
						   ),
						   tabPanel("Resource involvement",
						   		 navlistPanel(well = F,widths = c(2,9),
						   		 			 tabPanel("Resource",
						   		 			 		 plotOutput("resource_involvement_resource")
						   		 			 ),
						   		 			 tabPanel("Case",
						   		 			 		 plotOutput("resource_involvement_case")
						   		 			 ),
						   		 			 tabPanel("Resource-activity",
						   		 			 		 plotOutput("resource_involvement_resource_activity")
						   		 			 )

						   		 )
						   ),
						   		 tabPanel("Resource specialization",
						   		 		 navlistPanel(well = F,widths = c(2,9),
						   		 		 			 tabPanel("Log",
						   		 		 			 		 plotOutput("resource_specialization_log")
						   		 		 			 ),
						   		 		 			 tabPanel("Resource",
						   		 		 			 		 plotOutput("resource_specialization_resource")
						   		 		 			 ),
						   		 		 			 tabPanel("activity",
						   		 		 			 		 plotOutput("resource_specializationt_activity")
						   		 		 			 )
						   		 		 )
						   		 )
						   )

				)

		)
	)



		server <- function(input, output, session){
			output$resource_frequency_log <- renderPlot({
				eventlog %>%
					resource_frequency("log") %>%
					plot()
			})
			output$resource_frequency_case <- renderPlot({
				eventlog %>%
					resource_frequency("case") %>%
					plot()
			})
			output$resource_frequency_resource <- renderPlot({
				eventlog %>%
					resource_frequency("resource") %>%
					plot()
			})
			output$resource_frequency_activity <- renderPlot({
				eventlog %>%
					resource_frequency("activity") %>%
					plot()
			})
			output$resource_frequency_resource_activity <- renderPlot({
				eventlog %>%
					resource_frequency("resource-activity") %>%
					plot()
			})


			output$resource_involvement_resource <- renderPlot({
				eventlog %>%
					resource_involvement("resource") %>%
					plot()
			})
			output$resource_involvement_case <- renderPlot({
				eventlog %>%
					resource_involvement("case") %>%
					plot()
			})
			output$resource_involvement_resource_activity <- renderPlot({
				eventlog %>%
					resource_involvement("resource-activity") %>%
					plot()
			})


			output$resource_specialization_log <- renderPlot({
				eventlog %>%
					resource_specialisation("log") %>%
					plot()
			})
			output$resource_specialization_resource <- renderPlot({
				eventlog %>%
					resource_specialisation("resource") %>%
					plot()
			})
			output$resource_specializationt_activity <- renderPlot({
				eventlog %>%
					resource_specialisation("activity") %>%
					plot()
			})

			observeEvent(input$done, {
				stopApp()
			})
		}

		runGadget(shinyApp(ui, server), viewer = dialogViewer("Resource dashboard", height = 900, width = 1200))

}
