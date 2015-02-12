<style type="text/css">
img {
   width: 60%;
}
</style>
CSCI 3308 Methods & Tools
=========================

Project Vision Statement
------------------------

* **Who**: Daniel Noland, Conner Simmering, Taylor Thomas, Justin Olson, 
  Michael Muehlbradt

* **Title**: Memory Oracle

* **Description**: Web based front end to GDB which will provide intuitive
  visualization of the debugged program’s memory state.

* **Vision statement**: To enhance the usability of GDB and facilitate the
  instruction of programming, especially data structures.
  **[Live mockup here.](https://dnoland.com/vision/mockup.html)**
  ![Mockup still](mockup.png)

* **Motivation**: Facilitating faster software development times and improved
  code quality.

* **Risks**:

   - Allowing GDB to efficiently communicate with a web server / client may be difficult.

      - **Mitigation**: relax the project goals to require that the
        debugged code include helper code for the web debug features.

   - The GDB python api is sparsely used and very sparsely documented.
      
       - **Mitigation**: our entire target software stack is open source.  Thus
         we may examine its exact functionality at any time, even in the
         absence of quality documentation.

   - Most of our team members are unfamiliar with web development.
      
      - **Mitigation**: we can offload the web server deployment and page
        design to one of our team members who is familiar with web development
        should the learning curve prove unrealistic.

* **VCS**: Git

* **VCS Link**: [https://github.com/daniel-noland/MemoryOracle](https://github.com/daniel-noland/MemoryOracle)

