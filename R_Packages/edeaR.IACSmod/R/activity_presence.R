#' Metric: Activity Presence
#'
#'
#' Calculates for each activity type in what percentage of cases it is present.
#'
#' An indication of variance can be the presence of the activities in the different cases. This metric shows for each activity the absolute
#' number of cases in which each activity occurs together with its relative presence.
#'
#'
#'
#' @examples
#' \dontrun{
#' data <- data.frame(case = rep("A",5),
#' activity_id = c("A","B","C","D","E"),
#' activity_instance_id = 1:5,
#' lifecycle_id = rep("complete",5),
#' timestamp = 1:5,
#' resource = rep("resource 1", 5))
#'
#' log <- bupaR.IACSmod::eventlog(data,case_id = "case",
#' activity_id = "activity_id",
#' activity_instance_id = "activity_instance_id",
#' lifecycle_id = "lifecycle_id",
#' timestamp = "timestamp",
#' resource_id = "resource")
#'
#'activity_presence(log)
#' }
#'
#' @inherit activity_frequency params references return seealso
#'
#' @export activity_presence

activity_presence <- function(eventlog, append, append_column, sort, ...) {
	UseMethod("activity_presence")
}

#' @describeIn activity_presence Compute activity presence for event log
#' @export

activity_presence.eventlog <- function(eventlog,
									   append = F,
									   append_column = "absolute",
									   sort = TRUE,
									   ...)
	{
	absolute <- NULL

	if(is.null(append_column)) {
		append_column <- case_when(level == "activity" ~ "absolute",
								   level == "case" ~ "absolute",
								   T ~ "NA")
	}

	FUN <- activity_presence_FUN
	output <- FUN(eventlog = eventlog)

	if(sort) {
		output %>%
			arrange(-absolute) -> output
	}


	return_metric(eventlog, output, "activity", append, append_column, "activity_presence")
}

#' @describeIn activity_presence Compute activity presence for grouped eventlog
#' @export

activity_presence.grouped_eventlog <- function(eventlog,
											   append = F,
											   append_column = "absolute",
											   sort = TRUE,
											   ...) {
	absolute <- NULL
	FUN <- activity_presence_FUN
	output <- grouped_metric(eventlog, FUN)

	if(sort) {
		output %>%
			arrange(-absolute) -> output
	}

	return_metric(eventlog, output, "activity", append, append_column, "activity_presence")
}

activity_presence_FUN <- function(eventlog) {
	absolute <- NULL
	eventlog %>%
		group_by(!!as.symbol(activity_id(eventlog))) %>%
		summarize(absolute = n_distinct(!!as.symbol(case_id(eventlog)))) %>%
		mutate(relative = absolute/n_cases(eventlog))
}


