"""
basic view tests for the Flask application
"""
from flask import url_for
from app import db
from app.models import Project, ConfigTemplate, TemplateValueSet, TemplateValue, TemplateVariable
from tests import BaseFlaskTest


class CommonSiteTest(BaseFlaskTest):

    def test_redirect_of_the_homepage(self):
        """
        test redirect to homepage if connecting to the
        :return:
        """
        response = self.client.get("/")
        self.assertEqual(response.headers['Location'], "http://localhost%s" % url_for("home"))
        self.assertEqual(response.status_code, 302)

    def test_homepage_is_available(self):
        """
        just a simple test to avoid an error when accessing the homepage
        :return:
        """
        response = self.client.get(url_for("home"))
        self.assert200(response)


class ProjectViewTest(BaseFlaskTest):

    def setUp(self):
        # disable CSRF for unit testing
        super().setUp()
        self.app.config['WTF_CSRF_ENABLED'] = False

    def test_view_all_projects(self):
        """
        test view all projects page
        :return:
        """
        # test empty view
        response = self.client.get(url_for("view_all_projects"))
        self.assert200(response)
        self.assertTemplateUsed("project/view_all_projects.html")
        self.assertIn("No Projects found in database.", response.data.decode("utf-8"))

        # test view with elements
        project_names = [
            "My first Project",
            "My second Project",
            "My third Project",
        ]
        for name in project_names:
            p = Project(name)
            db.session.add(p)
            db.session.commit()

        response = self.client.get(url_for("view_all_projects"))
        self.assert200(response)
        self.assertTemplateUsed("project/view_all_projects.html")
        self.assertTrue(len(Project.query.all()) > 0)

        for name in project_names:
            self.assertIn(name, response.data.decode("utf-8"))

    def test_view_project_success(self):
        """
        test project view
        :return:
        """
        p = Project("My Project")
        db.session.add(p)
        db.session.commit()

        response = self.client.get(url_for("view_project", project_id=p.id))
        self.assert200(response)
        self.assertTemplateUsed("project/view_project.html")
        self.assertIn(p.name, response.data.decode("utf-8"))

    def test_view_project_404(self):
        """
        test project view not found
        :return:
        """
        response = self.client.get(url_for("view_project", project_id=9999))
        self.assert404(response)

    def test_add_project(self):
        """
        add new project
        :return:
        """
        project_name = "My Project"
        data = {
            "name": project_name
        }

        # add a new project
        response = self.client.post(url_for("edit_project"), data=data, follow_redirects=True)

        self.assert200(response)
        self.assertIn(project_name, response.data.decode("utf-8"))
        self.assertTemplateUsed("project/view_project.html")
        self.assertTrue(len(Project.query.all()) == 1)

        p = Project.query.filter(Project.name == project_name).first()

        self.assertIsNotNone(p, "Project not found and was therefore not created")
        self.assertEqual(p.name, project_name)

    def test_edit_project(self):
        """
        test edit of the project data object (including renaming of the project)
        :return:
        """
        project_name = "project name"
        conflicting_project_name = "conflicting project name"
        renamed_project_name = "renamed project name"
        p1 = Project(project_name)
        p2 = Project(conflicting_project_name)
        db.session.add_all([p1, p2])
        db.session.commit()

        # try to change the name of p1 (same name as p2)
        data = {
            "name": conflicting_project_name
        }
        response = self.client.post(url_for("edit_project", project_id=p1.id), data=data, follow_redirects=True)

        self.assert200(response)
        self.assertTemplateUsed("project/edit_project.html")
        self.assertTrue(len(Project.query.all()) == 2)
        self.assertIn("name already exist, please use another one", response.data.decode("utf-8"))

        p = Project.query.filter(Project.name == project_name).first()

        self.assertIsNotNone(p, "Project not found in database")
        self.assertEqual(p.name, project_name)

        # test rename project
        data = {
            "name": renamed_project_name
        }
        response = self.client.post(url_for("edit_project", project_id=p.id), data=data, follow_redirects=True)

        self.assert200(response)
        self.assertTemplateUsed("project/view_project.html")
        self.assertTrue(len(Project.query.all()) == 2)
        self.assertIn(renamed_project_name, response.data.decode("utf-8"))

        p = Project.query.filter(Project.name == renamed_project_name).first()

        self.assertIsNotNone(p, "Renamed Project not found in database")
        self.assertEqual(p.name, renamed_project_name)

    def test_edit_project_attributes(self):
        """
        test edit of the project attributes
        :return:
        """
        project_name = "project name"
        p = Project(project_name)
        db.session.add(p)
        db.session.commit()

        # test project edit form
        data = {
            "name": project_name
        }
        response = self.client.post(url_for("edit_project", project_id=p.id), data=data, follow_redirects=True)

        self.assert200(response)
        self.assertTemplateUsed("project/view_project.html")
        self.assertTrue(len(Project.query.all()) == 1)

    def test_delete_project_success(self):
        """
        test successful deletion operation on a project
        :return:
        """
        p = Project("My Project")
        db.session.add(p)
        db.session.commit()

        # delete the element
        response = self.client.post(url_for("delete_project", project_id=p.id), follow_redirects=True)
        self.assert200(response)
        self.assertTemplateUsed("project/view_all_projects.html")
        self.assertIn("All Projects", response.data.decode("utf-8"))
        self.assertTrue(len(Project.query.all()) == 0)

    def test_delete_project_failed(self):
        """
        test a failed deletion operation on a project
        :return:
        """
        response = self.client.get(url_for("delete_project", project_id=999), follow_redirects=True)
        self.assert404(response)


class ConfigTemplateViewTest(BaseFlaskTest):

    def setUp(self):
        # disable CSRF for unit testing
        super().setUp()
        self.app.config['WTF_CSRF_ENABLED'] = False

    def test_view_all_config_templates(self):
        """
        test view all config template page (integrated to the view project)
        :return:
        """
        project_name = "My Project"
        project_template_names = [
            "first template",
            "second template",
            "third template",
        ]
        ct_other_name = "template not visible in p1"
        p1 = Project(project_name)
        p2 = Project("My other Project")
        db.session.add_all([p1, p2])

        for name in project_template_names:
            ct = ConfigTemplate(name=name, project=p1)
            db.session.add(ct)
            db.session.commit()
        ct_other = ConfigTemplate(name=ct_other_name, project=p2)
        db.session.add(ct_other)
        db.session.commit()

        response = self.client.get(url_for("view_project", project_id=p1.id))
        self.assert200(response)
        self.assertTemplateUsed("project/view_project.html")
        self.assertTrue(len(Project.query.all()) >= 2)
        self.assertTrue(len(ConfigTemplate.query.all()) >= 4)

        for name in project_template_names:
            self.assertIn(name, response.data.decode("utf-8"))

        self.assertNotIn(ct_other_name, response.data.decode("utf-8"))

    def test_view_config_template_success(self):
        """
        test config template view
        :return:
        """
        var_1_name = "variable_1"
        var_1_desc = "description 1"
        var_2_name = "variable_2"
        var_2_desc = "description 2"

        p = Project("My Project")
        ct = ConfigTemplate("Template name", project=p)
        ct.update_template_variable(var_1_name, var_1_desc)
        ct.update_template_variable(var_2_name, var_2_desc)
        db.session.add(p)
        db.session.add(ct)
        db.session.commit()

        response = self.client.get(url_for("view_config_template", project_id=p.id, config_template_id=ct.id))
        self.assert200(response)
        self.assertTemplateUsed("config_template/view_config_template.html")
        self.assertIn(ct.name, response.data.decode("utf-8"))
        self.assertIn(var_1_name, response.data.decode("utf-8"))
        self.assertIn(var_1_desc, response.data.decode("utf-8"))
        self.assertIn(var_2_name, response.data.decode("utf-8"))
        self.assertIn(var_2_desc, response.data.decode("utf-8"))

    def test_view_config_template_404(self):
        """
        test config template view not found
        :return:
        """
        p = Project("My project")
        db.session.add(p)
        db.session.commit()
        response = self.client.get(
                url_for(
                    "view_config_template",
                    project_id=p.id,
                    config_template_id=9999
                )
        )
        self.assert404(response)

    def test_add_config_template(self):
        """
        add new config template
        :return:
        """
        p = Project("Name")
        db.session.add(p)
        db.session.commit()

        config_template_name = "My Template name"
        config_template_content = """!
!
! Test template
!
!"""
        data = {
            "name": config_template_name,
            "template_content": config_template_content
        }

        # add a new project
        response = self.client.post(url_for("edit_config_template", project_id=p.id), data=data, follow_redirects=True)

        self.assert200(response)
        self.assertIn(config_template_name, response.data.decode("utf-8"))
        self.assertIn(config_template_content, response.data.decode("utf-8"))
        self.assertTemplateUsed("config_template/view_config_template.html")
        self.assertTrue(len(Project.query.all()) == 1)

        ct = ConfigTemplate.query.filter(
                (ConfigTemplate.name == config_template_name) and
                (ConfigTemplate.project.id == p.id)
        ).first()

        self.assertIsNotNone(ct, "Config Template not found and was therefore not created")
        self.assertEqual(ct.name, config_template_name)

    def test_edit_config_template(self):
        """
        test edit of the config template data object (including renaming of the project)
        :return:
        """
        project_name = "project name"
        ct_name = "template name"
        ct_content = "content"
        changed_ct_content = "changed content"
        conflicting_ct_name = "conflicting config template name"
        renamed_ct_name = "renamed config template name"
        p = Project(project_name)
        db.session.add(p)

        ct1 = ConfigTemplate(name=ct_name, template_content=ct_content, project=p)
        ct2 = ConfigTemplate(name=conflicting_ct_name, template_content=ct_content, project=p)
        db.session.add_all([ct1, ct2])
        db.session.commit()

        # try to change the name of ct1 (same name as ct2)
        data = {
            "name": conflicting_ct_name,
            "template_content": ct_content
        }
        response = self.client.post(
            url_for(
                "edit_config_template",
                project_id=ct1.project.id,
                config_template_id=ct1.id),
            data=data,
            follow_redirects=True
        )

        self.assert200(response)
        self.assertTemplateUsed("config_template/edit_config_template.html")
        self.assertTrue(len(ConfigTemplate.query.all()) == 2)
        self.assertIn("name already exist, please use another one", response.data.decode("utf-8"))

        ct1 = ConfigTemplate.query.filter(
                (Project.id == p.id) and
                (ConfigTemplate.name == ct_name)
        ).first()

        self.assertIsNotNone(ct1, "Config Template not found in database")
        self.assertEqual(ct1.name, ct_name)
        self.assertEqual(ct1.template_content, ct_content)

        # test rename of Config Template
        data = {
            "name": renamed_ct_name,
            "template_content": changed_ct_content
        }
        response = self.client.post(
            url_for(
                "edit_config_template",
                project_id=ct1.project.id,
                config_template_id=ct1.id
            ),
            data=data,
            follow_redirects=True
        )

        self.assert200(response)
        self.assertTemplateUsed("config_template/view_config_template.html")
        self.assertTrue(len(ConfigTemplate.query.all()) == 2)
        self.assertIn(renamed_ct_name, response.data.decode("utf-8"))
        self.assertIn(changed_ct_content, response.data.decode("utf-8"))

        ct = ConfigTemplate.query.filter(
                (ConfigTemplate.name == renamed_ct_name) and
                (ConfigTemplate.project.id == p.id)
        ).first()

        self.assertIsNotNone(ct, "Renamed Config Template not found")
        self.assertEqual(ct.name, renamed_ct_name)

    def test_edit_config_template_attributes(self):
        """
        test edit of the config template attributes
        :return:
        """
        project_name = "project name"
        p = Project(project_name)
        db.session.add(p)
        db.session.commit()

        ct = ConfigTemplate(name="mytemplate", template_content="The is the content", project=p)
        db.session.add(ct)
        db.session.commit()

        new_ct_content = "other content than before"

        # test project edit form
        data = {
            "name": ct.name,
            "template_content": new_ct_content
        }
        response = self.client.post(
            url_for(
                "edit_config_template",
                project_id=p.id,
                config_template_id=ct.id
            ),
            data=data,
            follow_redirects=True
        )

        self.assert200(response)
        self.assertTemplateUsed("config_template/view_config_template.html")
        self.assertTrue(len(ConfigTemplate.query.all()) == 1)
        self.assertIn(new_ct_content, response.data.decode("utf-8"))

    def test_delete_config_template_success(self):
        """
        test successful deletion operation on a config template
        :return:
        """
        p = Project("My Project")
        ct1 = ConfigTemplate("config template", project=p)
        ct2 = ConfigTemplate("another config template", project=p)
        db.session.add_all([p, ct1, ct2])
        db.session.commit()
        self.assertTrue(len(ConfigTemplate.query.all()) == 2)

        # delete the element
        response = self.client.post(
                url_for(
                    "delete_config_template",
                    project_id=ct1.project.id,
                    config_template_id=ct1.id
                ),
                follow_redirects=True
        )
        self.assert200(response)
        self.assertTemplateUsed("project/view_project.html")
        self.assertIn("View Project", response.data.decode("utf-8"))
        self.assertTrue(len(ConfigTemplate.query.all()) == 1)
        self.assertTrue(len(Project.query.all()) == 1)

    def test_delete_config_template_failed(self):
        """
        test a failed deletion operation on a config template
        :return:
        """
        p = Project("My project")
        db.session.add(p)
        db.session.commit()
        response = self.client.get(url_for("delete_config_template", project_id=p.id, config_template_id=9999))
        self.assert404(response)

    def test_rename_variable_description_in_the_config_template(self):
        """
        rename a Config Template variable description using the form
        :return:
        """
        project_name = "project name"
        ct_name = "template name"
        ct_content = "content"
        changed_description = "changed description with some custom content"

        p = Project(project_name)
        db.session.add(p)

        ct = ConfigTemplate(name=ct_name, template_content=ct_content, project=p)
        ct.update_template_variable("var_1")
        db.session.add(ct)

        data = {
            "var_name_slug": "var_1",
            "description": changed_description
        }
        response = self.client.post(
            url_for(
                "edit_template_variable",
                config_template_id=ct.id,
                template_variable_id=ct.get_template_variable_by_name("var_1").id
            ),
            data=data,
            follow_redirects=True
        )

        self.assert200(response)
        self.assertTemplateUsed("config_template/view_config_template.html")
        self.assertTrue(len(TemplateVariable.query.all()) == 1)
        self.assertIn(changed_description, response.data.decode("utf-8"))

    def test_rename_of_a_variable_with_an_reserved_name(self):
        """
        the variable cannot be renamed to "hostname" because it is reserved
        :return:
        """
        project_name = "project name"
        ct_name = "template name"
        ct_content = "content"
        p = Project(project_name)
        db.session.add(p)

        ct = ConfigTemplate(name=ct_name, template_content=ct_content, project=p)
        ct.update_template_variable("var_1")
        db.session.add(ct)

        data = {
            "var_name_slug": "hostname"
        }
        response = self.client.post(
            url_for(
                "edit_template_variable",
                config_template_id=ct.id,
                template_variable_id=ct.get_template_variable_by_name("var_1").id
            ),
            data=data,
            follow_redirects=True
        )

        self.assert200(response)
        self.assertTemplateUsed("template_variable/edit_template_variable.html")
        self.assertTrue(len(TemplateVariable.query.all()) == 1)
        self.assertIn(
                "hostname is reserved by the application, please choose another one",
                response.data.decode("utf-8")
        )

    def test_rename_of_a_variable_within_the_config_template(self):
        """
        test rename of a template variable
        :return:
        """
        project_name = "project name"
        ct_name = "template name"
        ct_content = "content"
        p = Project(project_name)
        changed_var_name = "var_1_changed"
        db.session.add(p)

        ct = ConfigTemplate(name=ct_name, template_content=ct_content, project=p)
        ct.update_template_variable("var_1")
        db.session.add(ct)

        # try to change the name of a variables
        data = {
            "var_name_slug": changed_var_name
        }
        response = self.client.post(
            url_for(
                "edit_template_variable",
                config_template_id=ct.id,
                template_variable_id=ct.get_template_variable_by_name("var_1").id
            ),
            data=data,
            follow_redirects=True
        )

        self.assert200(response)
        self.assertTemplateUsed("config_template/view_config_template.html")
        self.assertTrue(len(TemplateVariable.query.all()) == 1)
        self.assertIn(changed_var_name, response.data.decode("utf-8"))


class TemplateValueSetViewTest(BaseFlaskTest):

    def setUp(self):
        # disable CSRF for unit testing
        super().setUp()
        self.app.config['WTF_CSRF_ENABLED'] = False

    def test_view_all_template_value_set(self):
        """
        test view all template value sets (integrated to the view config template)
        :return:
        """
        p = Project("Test")
        template_name = "My Project"
        tvs_names = [
            "first template",
            "second template",
            "third template",
        ]
        tvs_other_name = "template not visible in ct1"
        ct1 = ConfigTemplate(name=template_name, project=p)
        ct2 = ConfigTemplate(name="other config template", project=p)
        db.session.add_all([p, ct1, ct2])

        for name in tvs_names:
            tvs = TemplateValueSet(hostname=name, config_template=ct1)
            db.session.add(tvs)
            db.session.commit()
        tvs_other = TemplateValueSet(hostname=tvs_other_name, config_template=ct2)
        db.session.add(tvs_other)
        db.session.commit()

        response = self.client.get(url_for("view_config_template", project_id=p.id, config_template_id=ct1.id))
        self.assert200(response)
        self.assertTemplateUsed("config_template/view_config_template.html")
        self.assertTrue(len(Project.query.all()) == 1)
        self.assertTrue(len(ConfigTemplate.query.all()) == 2)
        self.assertTrue(len(TemplateValueSet.query.all()) == 4)

        for name in tvs_names:
            self.assertIn(name, response.data.decode("utf-8"))

        self.assertNotIn(tvs_other_name, response.data.decode("utf-8"))

    def test_view_template_value_set_success(self):
        """
        test template value set view
        :return:
        """
        p = Project("My Project")
        ct = ConfigTemplate("Template name", project=p)
        ct.update_template_variable(var_name="var 1")
        ct.update_template_variable(var_name="var 2")
        ct.update_template_variable(var_name="var 3")
        tvs1 = TemplateValueSet("Template 1", config_template=ct)
        tvs2 = TemplateValueSet("Template 2", config_template=ct)

        db.session.add_all([p, ct, tvs1, tvs2])
        db.session.commit()

        response = self.client.get(
            url_for(
                "view_template_value_set",
                config_template_id=ct.id,
                template_value_set_id=tvs1.id
            )
        )
        self.assert200(response)
        self.assertTemplateUsed("template_value_set/view_template_value_set.html")
        self.assertIn(tvs1.hostname, response.data.decode("utf-8"))
        self.assertIn("var_1", response.data.decode("utf-8"))
        self.assertIn("var_2", response.data.decode("utf-8"))

    def test_view_template_value_set_404(self):
        """
        test template value set view not found
        :return:
        """
        p = Project(name="Project")
        ct = ConfigTemplate(name="TemplateValueSet", project=p)
        db.session.add(p)
        db.session.add(ct)
        db.session.commit()
        response = self.client.get(
                url_for(
                    "view_template_value_set",
                    config_template_id=ct.id,
                    template_value_set_id=9999
                )
        )
        self.assert404(response)

    def test_add_template_value_set(self):
        """
        add new template value set
        :return:
        """
        p = Project("Name")
        ct = ConfigTemplate(name="Config Template", project=p)
        ct.update_template_variable("Key 1")
        ct.update_template_variable("Key 2")
        db.session.add_all([p, ct])
        db.session.commit()

        tvs_hostname = "Template Value set"
        data = {
            "hostname": tvs_hostname,
            "edit_hostname": tvs_hostname,
            "edit_key_1": "",
            "edit_key_2": ""
        }

        # add a new template value set
        response = self.client.post(
            url_for(
                "edit_template_value_set",
                project_id=ct.project.id,
                config_template_id=ct.id
            ),
            data=data,
            follow_redirects=True
        )

        self.assert200(response)
        self.assertIn(tvs_hostname, response.data.decode("utf-8"))
        self.assertTemplateUsed("config_template/view_config_template.html")
        self.assertTrue(len(TemplateValueSet.query.all()) == 1)

        tvs = TemplateValueSet.query.filter(
                (TemplateValueSet.hostname == tvs_hostname) and
                (TemplateValueSet.config_template.id == ct.id)
        ).first()

        self.assertIsNotNone(tvs, "Config Template not found and was therefore not created")
        self.assertEqual(tvs.hostname, tvs_hostname)
        self.assertTrue(tvs.is_value_defined("hostname"))
        self.assertEqual(tvs.get_template_value_by_name_as_string("hostname"), tvs.hostname)
        self.assertTrue(tvs.is_value_defined(tvs.convert_variable_name("Key 1")))
        self.assertTrue(tvs.is_value_defined(tvs.convert_variable_name("Key 2")))

    def test_edit_template_value_set(self):
        """
        test edit of the template value set data object (including renaming of the project)
        :return:
        """
        project_name = "project name"
        ct_name = "template name"
        ct_content = "content"
        tvs_name = "template value set"
        conflicting_tvs_name = "conflicting template value set"
        renamed_tvs_name = "renamed template value set"
        template_variables = (
            ("variable_1", "value for the first var"),
            ("variable_2", ""),
            ("variable_3", ""),
        )

        p = Project(project_name)
        db.session.add(p)

        ct = ConfigTemplate(name=ct_name, template_content=ct_content, project=p)
        for name, value in template_variables:
            # disable the automatic conversion of the variable name
            self.assertEqual(ct.update_template_variable(name, value, auto_convert_var_name=False), name)
        db.session.add(ct)

        tvs1 = TemplateValueSet(hostname=tvs_name, config_template=ct)
        tvs2 = TemplateValueSet(hostname=conflicting_tvs_name, config_template=ct)
        db.session.add_all([tvs1, tvs2])
        db.session.commit()

        # try to change the name of tvs1 to tvs2
        data = {
            "hostname": conflicting_tvs_name
        }
        response = self.client.post(
            url_for(
                "edit_template_value_set",
                config_template_id=tvs1.config_template.id,
                template_value_set_id=tvs1.id
            ),
            data=data,
            follow_redirects=True
        )

        self.assert200(response)
        self.assertTemplateUsed("template_value_set/edit_template_value_set.html")
        self.assertIn("name already exist, please use another one", response.data.decode("utf-8"))
        self.assertTrue(len(TemplateValueSet.query.all()) == 2)

        tvs1 = TemplateValueSet.query.filter(
                (ConfigTemplate.id == ct.id) and
                (TemplateValueSet.hostname == tvs_name)
        ).first()

        self.assertIsNotNone(tvs1, "Template value set not found in database")
        self.assertEqual(tvs1.hostname, tvs_name)
        self.assertTrue(len(tvs1.values.all()) == 3+1)      # hostname is automatically added

        # test rename of Config Template
        data = {
            "hostname": renamed_tvs_name,
            "edit_hostname": tvs_name,
            "edit_variable_1": tvs1.get_template_value_by_name_as_string("variable_1"),
            "edit_variable_2": tvs1.get_template_value_by_name_as_string("variable_2"),
            "edit_variable_3": tvs1.get_template_value_by_name_as_string("variable_3"),
        }
        response = self.client.post(
            url_for(
                "edit_template_value_set",
                config_template_id=tvs1.config_template.id,
                template_value_set_id=tvs1.id
            ),
            data=data,
            follow_redirects=True
        )

        self.assert200(response)
        self.assertNotIn("Template Value set was not created (unknown error)", response.data.decode("utf-8"))
        self.assertTemplateUsed("config_template/view_config_template.html")
        self.assertTrue(len(TemplateValueSet.query.all()) == 2)
        self.assertIn(renamed_tvs_name, response.data.decode("utf-8"))

        tvs = TemplateValueSet.query.filter(
                (TemplateValueSet.hostname == renamed_tvs_name) and
                (TemplateValueSet.config_template.id == ct.id)
        ).first()

        self.assertIsNotNone(tvs, "Renamed Config Template not found")
        self.assertEqual(tvs.hostname, renamed_tvs_name)

    def test_edit_template_value_set_attributes(self):
        """
        test edit of the template value set attributes
        :return:
        """
        project_name = "project name"
        ct_name = "template name"
        ct_content = "content"
        tvs_name = "template value set"
        conflicting_tvs_name = "conflicting template value set"
        renamed_tvs_name = "renamed template value set"
        template_variables = (
            ("variable_1", "value for the first var"),
            ("variable_2", ""),
            ("variable_3", ""),
        )

        p = Project(project_name)
        db.session.add(p)

        ct = ConfigTemplate(name=ct_name, template_content=ct_content, project=p)
        for name, value in template_variables:
            # disable the automatic conversion of the variable name
            self.assertEqual(ct.update_template_variable(name, value, auto_convert_var_name=False), name)
        db.session.add(ct)

        tvs1 = TemplateValueSet(hostname=tvs_name, config_template=ct)
        tvs2 = TemplateValueSet(hostname=conflicting_tvs_name, config_template=ct)
        db.session.add_all([tvs1, tvs2])
        db.session.commit()

        # test project edit form
        new_var_3_content = "other value than before"

        data = {
            "hostname": renamed_tvs_name,
            "edit_hostname": tvs_name,
            "edit_variable_1": tvs1.get_template_value_by_name_as_string("variable_1"),
            "edit_variable_2": tvs1.get_template_value_by_name_as_string("variable_2"),
            "edit_variable_3": new_var_3_content,
        }
        response = self.client.post(
            url_for(
                "edit_template_value_set",
                config_template_id=tvs1.config_template.id,
                template_value_set_id=tvs1.id
            ),
            data=data,
            follow_redirects=True
        )

        self.assert200(response)
        self.assertTemplateUsed("config_template/view_config_template.html")
        self.assertTrue(len(TemplateValueSet.query.all()) == 2)
        self.assertIn(new_var_3_content, response.data.decode("utf-8"))

    def test_delete_template_value_set_success(self):
        """
        test successful deletion operation on a template value set
        :return:
        """
        p = Project("My Project")
        ct = ConfigTemplate("config template", project=p)
        tvs1 = TemplateValueSet(hostname="Test 1", config_template=ct)
        tvs2 = TemplateValueSet(hostname="Test 2", config_template=ct)
        db.session.add_all([p, ct, tvs1, tvs2])
        db.session.commit()
        self.assertTrue(len(TemplateValueSet.query.all()) == 2)

        # delete the element
        response = self.client.post(
                url_for(
                    "delete_template_value_set",
                    config_template_id=ct.id,
                    template_value_set_id=tvs1.id
                ),
                follow_redirects=True
        )
        self.assert200(response)
        self.assertTemplateUsed("config_template/view_config_template.html")
        self.assertIn("View Config Template", response.data.decode("utf-8"))
        self.assertTrue(len(TemplateValueSet.query.all()) == 1)
        self.assertTrue(len(ConfigTemplate.query.all()) == 1)

    def test_delete_template_value_set_failed(self):
        """
        test a failed deletion operation on a template value set
        :return:s
        """
        p = Project(name="Project")
        ct = ConfigTemplate("config template", project=p)
        db.session.add(p)
        db.session.add(ct)
        db.session.commit()
        response = self.client.get(
            url_for(
                "delete_template_value_set",
                config_template_id=ct.id,
                template_value_set_id=9999
            )
        )
        self.assert404(response)