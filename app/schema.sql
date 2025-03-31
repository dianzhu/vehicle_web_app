DROP TABLE IF EXISTS Parts;
DROP TABLE IF EXISTS PartsPurchaseOrder;
DROP TABLE IF EXISTS Vendor;
DROP TABLE IF EXISTS VehicleColors;
DROP TABLE IF EXISTS Vehicle;
DROP TABLE IF EXISTS Colors;
DROP TABLE IF EXISTS Manufacturer;
DROP TABLE IF EXISTS VehicleType;
DROP TABLE IF EXISTS VehicleCondition;
DROP TABLE IF EXISTS Individual;
DROP TABLE IF EXISTS Company;
DROP TABLE IF EXISTS Customer;
DROP TABLE IF EXISTS ManagerUser;
DROP TABLE IF EXISTS SalesPersonUser;
DROP TABLE IF EXISTS InventoryClerkUser;
DROP TABLE IF EXISTS Users;

-- Tables
CREATE TABLE Users (
  UserName varchar(16) NOT NULL,
  Password varchar(25) NOT NULL,
  FirstName varchar(16) NOT NULL,
  LastName varchar(25) NOT NULL,

  PRIMARY KEY (UserName)
);

CREATE TABLE InventoryClerkUser (
  UserName varchar(16) NOT NULL,
  PRIMARY KEY (UserName),
  FOREIGN KEY (UserName) REFERENCES Users(UserName)
);

CREATE TABLE SalesPersonUser (
  UserName varchar(16) NOT NULL,
  PRIMARY KEY (UserName),
  FOREIGN KEY (UserName) REFERENCES Users(UserName)
);

CREATE TABLE ManagerUser (
  UserName varchar(16) NOT NULL,
  PRIMARY KEY (UserName),
  FOREIGN KEY (UserName) REFERENCES Users(UserName)
);

CREATE TABLE Customer (
  CustomerID varchar(25) NOT NULL,
  EmailAddress varchar(50),
  Phone varchar(10) NOT NULL,
  StreetAddress varchar(50) NOT NULL,
  City varchar(50) NOT NULL,
  State varchar(2) NOT NULL,
  PostalCode varchar(25) NOT NULL,
  CustomerType varchar(25) NOT NULL,

  PRIMARY KEY (CustomerID)
);

CREATE TABLE Company (
  TaxIDNumber varchar(25) NOT NULL,
  CompanyName varchar(16) NOT NULL,
  PrimaryContactFirstName varchar(25) NOT NULL,
  PrimaryContactLastName varchar(25) NOT NULL,
  PrimaryContactTitle varchar(25) NOT NULL,

  PRIMARY KEY (TaxIDNumber),
  FOREIGN KEY (TaxIDNumber) REFERENCES Customer(CustomerID)
);

CREATE TABLE Individual (
  DriverLicenseNumber varchar(25) NOT NULL,
  FirstName varchar(16) NOT NULL,
  LastName varchar(25) NOT NULL,

  PRIMARY KEY (DriverLicenseNumber),
  FOREIGN KEY (DriverLicenseNumber) REFERENCES Customer(CustomerID)
);

CREATE TABLE VehicleType (
 Type  varchar(25)  NOT NULL,
 PRIMARY KEY (Type)
);

CREATE TABLE VehicleCondition (
    VehicleCondition varchar(25) NOT NULL,
    PRIMARY KEY (VehicleCondition)
);

CREATE TABLE Colors (
    Color varchar(25) NOT NULL,
    PRIMARY KEY (Color)
);

CREATE TABLE Manufacturer (
  ManufacturerName varchar(25) NOT NULL,
  PRIMARY KEY (ManufacturerName)
);

CREATE TABLE Vehicle (
  VIN  varchar(17)  NOT NULL,
  ModelYear varchar(25) NOT NULL,
  ModelName varchar(50) NOT NULL,
  Type varchar(25) NOT NULL,
  Description varchar(250),
  Mileage int(8) NOT NULL,
  FuelType varchar(25) NOT NULL,
  ManufacturerName varchar(25) NOT NULL,
  VehicleCondition varchar(25) NOT NULL,
  PurchasedFrom varchar(25)     NOT NULL,
  PurchaseDate  date         NOT NULL,
  PurchaseValue float         NOT NULL,
  EnteredBy     varchar(16)     NOT NULL,
  SoldTo        varchar(25),
  SoldDate      date,
  SalesPrice    float,
  SoldBy        varchar(16),

  PRIMARY KEY (VIN),
  FOREIGN KEY (ManufacturerName) REFERENCES Manufacturer(ManufacturerName),
  FOREIGN KEY (Type) REFERENCES VehicleType(Type),
  FOREIGN KEY (PurchasedFrom) REFERENCES Customer(CustomerID),
  FOREIGN KEY (EnteredBy) REFERENCES InventoryClerkUser(UserName),
  FOREIGN KEY (SoldTo) REFERENCES Customer(CustomerID),
  FOREIGN KEY (SoldBy) REFERENCES SalesPersonUser(UserName),
  FOREIGN KEY (VehicleCondition) REFERENCES VehicleCondition(VehicleCondition)
);

CREATE TABLE VehicleColors (
  VIN  varchar(17)  NOT NULL,
  Color varchar(16) NOT NULL,

  PRIMARY KEY (VIN, Color),
  FOREIGN KEY (VIN) REFERENCES Vehicle(VIN),
  FOREIGN KEY (Color) REFERENCES Colors(Color)
);

CREATE TABLE Vendor (
  VendorName varchar(25) NOT NULL,
  VendorPhoneNumber varchar(25) NOT NULL,
  StreetAddress varchar(50) NOT NULL,
  City varchar(50) NOT NULL,
  State varchar(2) NOT NULL,
  PostalCode varchar(25) NOT NULL,

  PRIMARY KEY (VendorName)
);

CREATE TABLE Parts (
  VIN varchar(17) NOT NULL,
  PartNumber  varchar(25) NOT NULL,
  POSequence    varchar(3) NOT NULL,
  VendorName varchar(25) NOT NULL,
  Description varchar(250) NOT NULL,
  Quantity varchar(50) NOT NULL,
  Status varchar(50) NOT NULL,
  Price float(15,2) NOT NULL,

  PRIMARY KEY (VIN, POSequence, PartNumber),
  FOREIGN KEY (VIN) REFERENCES Vehicle(VIN),
  FOREIGN KEY (VendorName) REFERENCES Vendor(VendorName)
);

INSERT INTO Manufacturer
    (ManufacturerName)
VALUES
    ('Acura'), ('FIAT'), ('Lamborghini'), ('Nio'),
    ('Alfa Romeo'), ('Ford'), ('Land Rover'), ('Porsche'),
    ('Aston Martin'), ('Geeley'), ('Lexus'), ('Ram'),
    ('Audi'), ('Genesis'), ('Lincoln'), ('Rivian'),
    ('Bentley'), ('GMC'), ('Lotus'), ('Rolls-Royce'),
    ('BMW'), ('Honda'), ('Maserati'), ('smart'),
    ('Buick'), ('Hyundai'), ('MAZDA'), ('Subaru'),
    ('Cadillac'), ('INFINITI'), ('McLaren'), ('Tesla'),
    ('Chevrolet'), ('Jaguar'), ('Mercedes-Benz'), ('Toyota'),
    ('Chrysler'), ('Jeep'), ('MINI'), ('Volkswagen'),
    ('Dodge'), ('Karma'), ('Mitsubishi'), ('Volvo'),
    ('Ferrari'), ('Kia'), ('Nissan'), ('XPeng');

INSERT INTO Colors
    (Color)
VALUES
    ('Aluminum'), ('Beige'), ('Black'), ('Blue'), ('Brown'), ('Bronze'), ('Claret'),
    ('Copper'), ('Cream'), ('Gold'), ('Gray'), ('Green'), ('Maroon'), ('Metallic'),
    ('Navy'), ('Orange'), ('Pink'), ('Purple'), ('Red'), ('Rose'), ('Rust'),
    ('Silver'), ('Tan'), ('Turquoise'), ('White'), ('Yellow');

INSERT INTO VehicleType
    (Type)
VALUES
    ('Sedan'), ('Coupe'), ('Convertible'), ('Truck'),
    ('Van'), ('Minivan'), ('SUV'), ('Other');

INSERT INTO VehicleCondition
    (VehicleCondition)
VALUES
    ('Excellent'), ('Very Good'), ('Good'), ('Fair');