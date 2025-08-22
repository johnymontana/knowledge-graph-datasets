// Neo4j Schema for Foursquare Data
// Neo4j constraints and indexes for Foursquare transit stops and places data

// Create constraints for unique identifiers
CREATE CONSTRAINT transit_stop_id_unique IF NOT EXISTS FOR (ts:TransitStop) REQUIRE ts.stop_id IS UNIQUE;
CREATE CONSTRAINT place_id_unique IF NOT EXISTS FOR (p:Place) REQUIRE p.fsq_place_id IS UNIQUE;
CREATE CONSTRAINT category_id_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.category_id IS UNIQUE;

// Create geospatial indexes for location-based queries
CREATE INDEX transit_stop_location IF NOT EXISTS FOR (ts:TransitStop) ON (ts.stop_lat, ts.stop_lon);
CREATE INDEX place_location IF NOT EXISTS FOR (p:Place) ON (p.latitude, p.longitude);

// Create Point indexes for advanced spatial queries (Neo4j 3.4+)
CREATE INDEX transit_stop_point IF NOT EXISTS FOR (ts:TransitStop) ON (ts.location);
CREATE INDEX place_point IF NOT EXISTS FOR (p:Place) ON (p.location);

// Create indexes for text-based queries
CREATE INDEX place_name IF NOT EXISTS FOR (p:Place) ON p.name;
CREATE INDEX transit_stop_name IF NOT EXISTS FOR (ts:TransitStop) ON ts.stop_name;
CREATE INDEX category_label IF NOT EXISTS FOR (c:Category) ON c.label;

// Create indexes for filtering and grouping
CREATE INDEX place_locality IF NOT EXISTS FOR (p:Place) ON p.locality;
CREATE INDEX place_region IF NOT EXISTS FOR (p:Place) ON p.region;
CREATE INDEX place_postcode IF NOT EXISTS FOR (p:Place) ON p.postcode;
CREATE INDEX transit_stop_zone IF NOT EXISTS FOR (ts:TransitStop) ON ts.zone_id;

// Create composite indexes for common query patterns
CREATE INDEX place_location_locality IF NOT EXISTS FOR (p:Place) ON (p.locality, p.latitude, p.longitude);

// Node labels and their purposes:
// - TransitStop: Transit stops and stations from King County Metro
// - Place: Points of interest from Foursquare API
// - Category: Foursquare place categories

// Relationship types:
// - BELONGS_TO_CATEGORY: Place belongs to Category
// - NEAR_STOP: Place is near a specific TransitStop (named relationship)
// - WITHIN_500M: Place is within 500 meters of TransitStop (spatial relationship)
// - WITHIN_WALKING_DISTANCE: Places within typical walking distance (800m)

// Additional spatial relationships can be created based on distance:
// - WITHIN_100M: Very close proximity
// - WITHIN_1KM: Nearby locations
// - SAME_LOCALITY: Places in the same city/locality