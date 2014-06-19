"""TO-DO: Write a description of what this XBlock is."""

import json

import pkg_resources
from mako.template import Template
from mako.lookup import TemplateLookup

from xblock.core import XBlock
from xblock.fields import Scope, Integer, String, BlockScope, List
from xblock.fragment import Fragment

class HelpResource(dict):
    def __str__(self):
        return json.dumps(self)
    def __init__(s):
        if isinstance(s, str):
            self.update(json.loads(s))
        elif isinstance(s, dict):
            self.update(s)
        else:
            raise TypeError("Inappropriate type "+str(type(s))+" initializing HelpResource. Should be str or dict")
        for e,t in (('id', int), ('title', str), ('url', str), ('upvotes', int), ('downvotes', int), ('description', str)):
            if e not in self:
                raise TypeError("Insufficient fields initializing HelpResource. "+e+" required.")
            if not isinstance(self["e"], t):
                raise TypeError("Incorrect field type initializing HelpResource. "+e+" should be "+str(t)+". It is "+type(self[e]))

    @property
    def title(self):
        return self["title"]
    @title.setter
    def title(self, newtitle):
        self["title"] = newtitle
    @property
    def url(self):
        return self["url"]
    @url.setter
    def url(self, newurl):
        self["url"] = newurl
    @property
    def upvotes(self):
        return self["upvotes"]
    @upvotes.setter
    def upvotes(self, newupvotes):
        self["upvotes"] = newupvotes
    @property
    def downvotes(self):
        return self["downvotes"]
    @downvotes.setter
    def downvotes(self, newdownvotes):
        self["downvotes"] = newdownvotes

class RecommenderXBlock(XBlock):
    """
    This XBlock will show a set of recommended resources
    """
    # Scope-wide. List of JSON objects corresponding to recommendations combine XML and user. 
    default_recommendations = List(help="List of help resources", default=[], scope=Scope.content)
    # Scope-wide. List of JSON objects corresponding to recommendations as defined in XML. 
    recommendations = List(help="List of help resources", default=[], scope=Scope.user_state_summary)
    # Upvotes for this particular user
    upvotes = List(help="List of items user gave upvote to", default=[], scope=Scope.user_state)
    # Downvotes for this particular user
    downvotes = List(help="List of items user gave downvote to", default=[], scope=Scope.user_state)

    template_lookup = None

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def getResourceNewId(self):
        recoms = self.recommendations
        if not recoms:
            recoms = self.default_recommendations
        resourceId = -1
        for recom in recoms:
            if recom['id'] > resourceId:
                resourceId = recom['id']
        return resourceId + 1

    def getRecommendationIndex(self, recomId):
        recoms = self.recommendations
        if not recoms:
            recoms = self.default_recommendations
        for idx in range(0, len(recoms)):
            if recoms[idx]['id'] == recomId:
                return idx
        return -1

    @XBlock.json_handler
    def handle_upvote(self, data, suffix=''):
      ''' untested '''
      resource = data['resource']
      idx = self.getRecommendationIndex(resource)
      if resource in self.upvotes:
        del self.upvotes[self.upvotes.index(resource)]
        self.recommendations[idx]['upvotes'] -= 1
      elif resource in self.downvotes:
        del self.downvotes[self.downvotes.index(resource)]
        self.recommendations[idx]['downvotes'] -= 1
        self.upvotes.append(resource)
        self.recommendations[idx]['upvotes'] += 1
      else:
        self.upvotes.append(resource)
        self.recommendations[idx]['upvotes'] += 1
      print "Upvote clicked!"
      return {"Success": True}

    @XBlock.json_handler
    def handle_downvote(self, data, suffix=''):
      ''' untested '''
      resource = data['resource']
      idx = self.getRecommendationIndex(resource)
      if resource in self.downvotes:
        del self.downvotes[self.downvotes.index(resource)]
        self.recommendations[idx]['downvotes'] -= 1
      elif resource in self.upvotes:
        del self.upvotes[self.upvotes.index(resource)]
        self.recommendations[idx]['upvotes'] -= 1
        self.downvotes.append(resource)
        self.recommendations[idx]['downvotes'] += 1
      else:
        self.downvotes.append(resource)
        self.recommendations[idx]['downvotes'] += 1
      print "Downvote clicked!"
      return {"Success": True}


    @XBlock.json_handler
    def add_resource(self, data, suffix=''):
        ''' untested '''
        resource = data['resource']
        # check url for redundancy
        recoms = self.recommendations
        #if not recoms:
        #    recoms = self.default_recommendations
        for recom in recoms:
            if recom['url'] == data['resource']['url']:
                print "add redundant resource"
                return {"Success": False}

        # Construct new resource
        valid_fields = ['url', 'title', 'description']
        new_resource = {}
        for field in valid_fields:
            new_resource[field] = data['resource'][field]
        new_resource['upvotes'] = 0
        new_resource['downvotes'] = 0
        new_resource['id'] = self.getResourceNewId()
        new_resource['isProblematic'] = "notProblematic"
        new_resource['problematicReason'] = ""
        print "before append"
#        self.resources.append(new_resource)
        self.recommendations.append(new_resource)
        print "after append"
        return {"Success": True, "id": new_resource['id']}

    @XBlock.json_handler
    def edit_resource(self, data, suffix=''):
        resource = data['resource']
        idx = self.getRecommendationIndex(resource)
        if idx not in range(0, len(self.recommendations)):
            print "Edit failed!"
            return {"Success": False}
        # check url for redundancy
        recoms = self.recommendations
        for recom in recoms:
            if recom['url'] == data['url']:
                print "edit to esisting resource"
                return {"Success": False}

        for key in data:
          if key == 'resource':
            next
          if data[key] == '':
            next
          self.recommendations[idx][key] = data[key]
        return {"Success": True}

    @XBlock.json_handler
    def flag_resource(self, data, suffix=''):
        resource = data['resource']
        idx = self.getRecommendationIndex(resource)
        if idx not in range(0, len(self.recommendations)):
            print "Flag failed!"
            return {"Success": False}

        self.recommendations[idx]['isProblematic'] = data['isProblematic']
        return {"Success": True}

    # TO-DO: change this view to display your data your own way.
    def student_view(self, context=None):
        """
        The primary view of the RecommenderXBlock, shown to students
        when viewing courses.
        """
        print "entered"
        if not self.recommendations:
            self.recommendations = self.default_recommendations
        if not self.recommendations:
            self.recommendations = []

        if not self.template_lookup:
            self.template_lookup = TemplateLookup() 
            self.template_lookup.put_string("recommender.html", self.resource_string("static/html/recommender.html"))
            self.template_lookup.put_string("resourcebox.html", self.resource_string("static/html/resourcebox.html"))

        # TODO: Sort by votes
        # Ideally, we'd estimate score based on votes, such that items with 1 vote have a sensible ranking (rather than a perfect rating)
        # 
        resources = [{'id' : r['id'], 'title' : r['title'], "votes" : r['upvotes'] - r['downvotes'], 'url' : r['url'], 'description' : r['description'], 'isProblematic': r['isProblematic'], 'problematicReason': r['problematicReason']} for r in self.recommendations]
        resources = sorted(resources, key = lambda r: r['votes'], reverse=True)

        frag = Fragment(self.template_lookup.get_template("recommender.html").render(resources = resources, upvotes = self.upvotes, downvotes = self.downvotes))
        frag.add_css_url("//ajax.googleapis.com/ajax/libs/jqueryui/1.10.4/themes/smoothness/jquery-ui.css")
        frag.add_css_url("//code.jquery.com/ui/1.10.4/themes/smoothness/jquery-ui.css")
        frag.add_javascript_url("//ajax.googleapis.com/ajax/libs/jqueryui/1.10.4/jquery-ui.min.js")
        frag.add_css(self.resource_string("static/css/recommender.css"))
        frag.add_javascript(self.resource_string("static/js/src/recommender.js"))
        frag.initialize_js('RecommenderXBlock')
        return frag

    # TO-DO: change this to create the scenarios you'd like to see in the
    # workbench while developing your XBlock.
    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("RecommenderXBlock",
             """<vertical_demo>
               <html_demo><img class="question" src="http://people.csail.mit.edu/swli/edx/recommendation/img/pset.png"></img></html_demo> 
               <recommender> 
                     {"id": 1, "title": "Covalent bonding and periodic trends", "upvotes" : 15, "downvotes" : 5, "url" : "https://courses.edx.org/courses/MITx/3.091X/2013_Fall/courseware/SP13_Week_4/SP13_Periodic_Trends_and_Bonding/", "description" : "http://people.csail.mit.edu/swli/edx/recommendation/img/videopage1.png", "isProblematic": "notProblematic", "problematicReason": ""}
                     {"id": 2, "title": "Polar covalent bonds and electronegativity", "upvotes" : 10, "downvotes" : 7, "url" : "https://courses.edx.org/courses/MITx/3.091X/2013_Fall/courseware/SP13_Week_4/SP13_Covalent_Bonding/", "description" : "http://people.csail.mit.edu/swli/edx/recommendation/img/videopage2.png", "isProblematic": "notProblematic", "problematicReason": ""}
                     {"id": 3, "title": "Longest wavelength able to to break a C-C bond ...", "upvotes" : 1230, "downvotes" : 7, "url" : "https://answers.yahoo.com/question/index?qid=20081112142253AA1kQN1", "description" : "http://people.csail.mit.edu/swli/edx/recommendation/img/dispage1.png", "isProblematic": "notProblematic", "problematicReason": ""}
                     {"id": 4, "title": "Calculate the maximum wavelength of light for ...", "upvotes" : 10, "downvotes" : 3457, "url" : "https://answers.yahoo.com/question/index?qid=20100110115715AA6toHw", "description" : "http://people.csail.mit.edu/swli/edx/recommendation/img/dispage2.png", "isProblematic": "notProblematic", "problematicReason": ""}
                  </recommender>
                </vertical_demo>
             """),
#                     {"id": 5, "title": "Covalent bond - wave mechanical concep", "upvotes" : 10, "downvotes" : 7, "url" : "", "description" : "http://people.csail.mit.edu/swli/edx/recommendation/img/textbookpage1.png", "isProblematic": "notProblematic"}
#                     {"id": 6, "title": "Covalent bond - Energetics of covalent bond", "upvotes" : 10, "downvotes" : 7, "url" : "", "description" : "http://people.csail.mit.edu/swli/edx/recommendation/img/textbookpage2.png", "isProblematic": "notProblematic"}
#                  </recommender>
#                </vertical_demo>
#             """),
        ]

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """
        Parse the XML for an HTML block.

        The entire subtree under `node` is re-serialized, and set as the
        content of the XBlock.

        """
        block = runtime.construct_xblock_from_class(cls, keys)
        lines = []
        for line in node.text.split('\n'):
            line = line.strip()
            if len(line) > 2:
                print "Decoding", line
                lines.append(json.loads(line))
    
        block.default_recommendations = lines
        return block
