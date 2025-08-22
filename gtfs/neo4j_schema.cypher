// Neo4j Schema for GTFS Data
// Neo4j constraints and indexes for GTFS transit data

// Create constraints for unique identifiers
CREATE CONSTRAINT agency_id_unique IF NOT EXISTS FOR (a:Agency) REQUIRE a.agency_id IS UNIQUE;
CREATE CONSTRAINT route_id_unique IF NOT EXISTS FOR (r:Route) REQUIRE r.route_id IS UNIQUE;
CREATE CONSTRAINT stop_id_unique IF NOT EXISTS FOR (s:Stop) REQUIRE s.stop_id IS UNIQUE;
CREATE CONSTRAINT trip_id_unique IF NOT EXISTS FOR (t:Trip) REQUIRE t.trip_id IS UNIQUE;
CREATE CONSTRAINT service_id_unique IF NOT EXISTS FOR (c:Calendar) REQUIRE c.service_id IS UNIQUE;
CREATE CONSTRAINT fare_id_unique IF NOT EXISTS FOR (f:FareAttribute) REQUIRE f.fare_id IS UNIQUE;

// Create indexes for performance
CREATE INDEX stop_location IF NOT EXISTS FOR (s:Stop) ON (s.stop_lat, s.stop_lon);
CREATE INDEX route_type IF NOT EXISTS FOR (r:Route) ON r.route_type;
CREATE INDEX trip_route IF NOT EXISTS FOR (t:Trip) ON t.route_id;
CREATE INDEX stop_time_trip IF NOT EXISTS FOR (st:StopTime) ON st.trip_id;
CREATE INDEX stop_time_stop IF NOT EXISTS FOR (st:StopTime) ON st.stop_id;
CREATE INDEX calendar_service IF NOT EXISTS FOR (c:Calendar) ON c.service_id;

// Node labels will be:
// - Agency: Transit agencies
// - Route: Transit routes  
// - Stop: Transit stops/stations
// - Trip: Individual trips
// - StopTime: Stop times for trips
// - Calendar: Service calendar
// - CalendarDate: Service exceptions
// - FareAttribute: Fare information
// - FareRule: Fare rules
// - Transfer: Transfer rules
// - Shape: Route shapes
// - FeedInfo: Feed information

// Relationship types:
// - OPERATES: Agency operates Route
// - SERVES: Route serves Stop (via Trip)
// - BELONGS_TO: Trip belongs to Route
// - FOLLOWS: Trip follows Calendar
// - STOPS_AT: Trip stops at Stop (via StopTime)
// - CONNECTS_TO: Stop connects to Stop (via Transfer)
// - HAS_SHAPE: Trip has Shape