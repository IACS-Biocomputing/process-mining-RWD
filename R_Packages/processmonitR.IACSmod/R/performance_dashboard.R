


#' Performance Dashboard
#'
#' @param eventlog Event log to be used for dashboard
#'
#' @export
#'
performance_dashboard <- function(eventlog) {

	ui <- miniPage(
		gadgetTitleBar("Performance dashboard"),
		miniContentPanel(
			fillCol(flex = c(10,1),
					navbarPage("",
							   tabPanel("Throughput time",
							   		 navlistPanel(well = F,widths = c(2,9),
							   		 			 tabPanel("Log",
							   		 			 		 plotOutput("throughput_time_log")
							   		 			 ),
							   		 			 tabPanel("Case",
							   		 			 		 plotOutput("throughput_time_case")
							   		 			 )
							   		 )
							   ),
							   tabPanel("Processing time",
							   		 navlistPanel(well = F,widths = c(2,9),
							   		 			 tabPanel("Log",
							   		 			 		 plotOutput("processing_time_log")
							   		 			 ),
							   		 			 tabPanel("Case",
							   		 			 		 plotOutput("processing_time_case")
							   		 			 ),
							   		 			 tabPanel("Activity",
							   		 			 		 plotOutput("processing_time_activity")
							   		 			 ),
							   		 			 tabPanel("Resource",
							   		 			 		 plotOutput("processing_time_resource")
							   		 			 )
							   		 )
							   ),
							   tabPanel("Idle time",
							   		 navlistPanel(well = F,widths = c(2,9),
							   		 			 tabPanel("Log",
							   		 			 		 plotOutput("idle_time_log")
							   		 			 ),
							   		 			 tabPanel("Case",
							   		 			 		 plotOutput("idle_time_case")
							   		 			 ),
							   		 			 tabPanel("Resource",
							   		 			 		 plotOutput("idle_time_resource")
							   		 			 )
							   		 )
							   )
					),
					selectizeInput("units", "Time units:", choices = c("min","hours","days","weeks"), selected = "hours")

			)
		)
	)



	server <- function(input, output, session){
		output$throughput_time_log <- renderPlot({
			eventlog %>%
				throughput_time("log", units = input$units) %>%
				plot()
		})
		output$throughput_time_case <- renderPlot({
			eventlog %>%
				throughput_time("case", units = input$units) %>%
				plot()
		})
		output$processing_time_log <- renderPlot({
			eventlog %>%
				processing_time("log", units = input$units) %>%
				plot()
		})
		output$processing_time_case <- renderPlot({
			eventlog %>%
				processing_time("case", units = input$units) %>%
				plot()
		})
		output$processing_time_activity <- renderPlot({
			eventlog %>%
				processing_time("activity", units = input$units) %>%
				plot()
		})
		output$processing_time_resource <- renderPlot({
			eventlog %>%
				processing_time("resource", units = input$units) %>%
				plot()
		})
		output$idle_time_log <- renderPlot({
			eventlog %>%
				idle_time("log", units = input$units) %>%
				plot()
		})
		output$idle_time_case <- renderPlot({
			eventlog %>%
				idle_time("case", units = input$units) %>%
				plot()
		})
		output$idle_time_resource <- renderPlot({
			eventlog %>%
				idle_time("resource", units = input$units) %>%
				plot()
		})

		observeEvent(input$done, {
			stopApp()
		})
	}

	runGadget(shinyApp(ui, server), viewer = dialogViewer("Performance dashboard", height = 900, width = 1200))

}
