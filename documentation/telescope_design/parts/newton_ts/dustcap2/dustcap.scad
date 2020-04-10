difference() {
    union() {
        difference() {
            difference() {
                scale (2.18) {
                    import("./TelescopeDustCap-for-INDI-ServoBlasterCap.stl", convexity = 5);
                }
                cylinder(h = 42, r1 = 252, r2 = 252);
            }
            translate([289,-2.2,0]) {
                rotate([0,-70,0]) {
                    minkowski() {
                        cube(size = [37,8.8,23], center = false);
                        rotate([90,0,0]) {
                            cylinder(h = 0.001, r=3);
                        }
                    }
                }
            }
        }

        translate([296,-2.2,22]) {
            rotate([0,-70,0]) {
                translate([0,0,0]) {
                    minkowski() {
                        cube(size = [33.8,8.8,13], center = false);
                        rotate([90,0,0]) {
                            cylinder(h = 0.001, r=3);
                        }
                    }
                }
            }
        }

        difference() {
            translate([283,-5,41.6]) {
                rotate([0,-70,0]) {
                    translate([-5,2.8,-5]) {
                        cube(size=[10,8.8,10]);;
                    }
                }
            }
            translate([283,-5,41.6]) {
                rotate([0,-70,0]) {
                    translate([-4.8,-5,-0.5]) {
                        minkowski() {
                            cube(size=[5,25,5]);
                                rotate([90,0,0]) {
                                    cylinder(h = 0.001, r=3);
                                }
                        }
                    }
                }
            }
        }
    }

    // empreinte bras levier
    translate([280,2.75,-0.5]) {
        rotate([90,20,0]) {
            translate([0,20,0]) {
                cylinder(h = 5, r=7.6);

                minkowski() {
                    cube(size=[0.01,24,5]);
                    rotate([0,0,0]) {
                        cylinder(h = 0.001, r=3.6);
                    }
                }

                // arrondi 1
                difference() {
                    translate([-4,7,0]) {
                        cylinder(h=5, r=1);
                    }
                    translate([-6,8,-1]) {
                        cylinder(h=7, r=2.5);
                    }
                }
                
                // arrondi 2
                difference() {
                    translate([4,7,0]) {
                        cylinder(h=5, r=1);
                    }
                    translate([6,8,-1]) {
                        cylinder(h=7, r=2.5);
                    }
                }
            }
        }
    }
}
