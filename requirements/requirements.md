Project Requirements
====================

CSCI3308 Spring 2015
--------------------

* **Title**:
   Memory Oracle

* **Vision statement**: To enhance the usability of GDB and facilitate the
  instruction of programming, especially data structures.
  **[Live mockup here.](https://dnoland.com/vision/mockup.html)**
  ![Mockup still](mockup.png)

* **Who**: Daniel Noland, Conner Simmering, Taylor Thomas, Justin Olson, 
  Michael Muehlbradt

* **List of Requirements**:

   - *Business Requirements*: 
      
      - As a business, we want to be able to debug Linux compatible software
        written in C++ using only GDB and other free and open source tools so that
        we can write software without paying licensing fees.

   - *User Requirements*:
      
      - As a user, I want to be able to see a dynamic graphical display of the
        memory state of my program as it runs so that I can understand bugs
        quickly.

      - As a user, I want to be able to interact with GDB using its normal
        scripting language, so that I don't need to learn a new way of
        controlling my debugger.

   - *Functional Requirements*:

      - As a user, I want to be able to keep the input and output of GDB
        distinct from the input and output of my program so that I can easily
        debug arbitrary terminal based programs.

      - As a user, I want to be able to view my source code and the next line
        to be executed from within the debugger interface so that I can easily
        understand my program's control flow.

      - As a user, I want to be able to see the current scope's local variables
        and their values so that I may better understand the behavior of each
        function I write.

      - As a user, I want the web interface to display the debugee's memory
        state even if the debugee program crashes or exits abnormally so that I
        may study the abnormal behavior without manually loading core dump files.


   - *Non-Functional Requirements*:

      - As a user, I want to be able to debug software without exposing my
        computer to security vulnerabilities.

      - As a user, I want the debugger interface to continue to function with
        low (less than one second) of latency even while the debugee program is
        not paused so that I may continue working even while the debugee is in a
        blocking state.

* **Methodology**: Agile

* **Project Tracking Software**: Trac

* **
